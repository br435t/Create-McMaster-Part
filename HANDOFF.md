# Handoff — NX Open "Create Part" automation

Automates creating a new part in **NX 2506** running in **Teamcenter managed mode**,
prompting the user for a name and description via a BlockStyler dialog.

## Environment

- **NX 2506**, Python (CPython) journals run via **File → Execute → NX Open…**.
- Runs in **Teamcenter managed mode** (not native/filesystem mode). This changes
  everything about how parts are created (see gotchas).
- Custom Helion item types: `BE9_Design, BE9_Electrical, BE9_COTS, BE9_Tooling`
  (the part is created as `BE9_Design`).
- Default template: `@DB/model-plain-1-inch-template/A` (units = inches).
- An `nxopen` MCP server (see `.mcp.json`) indexes the NX 2506 Python API and
  stubs — use it to look up signatures. **Note:** it does **not** index
  `NXOpen.UF` (that subsystem has no stubs on disk).

## Files

| File | Purpose |
|------|---------|
| `create_part.py` | **Design** part. Prompts (BlockStyler dialog), then creates a `BE9_Design` item with an auto-assigned part number. |
| `create_part_dialog.dlx` | BlockStyler dialog layout (Name + Description fields). Must sit next to `create_part.py`. |
| `create_COTS_part.py` | **COTS/vendor** part (clean, reusable module mirroring `create_part.py`). Creates a `BE9_COTS` item with a user-supplied part number, and scrapes McMaster property data (log-only for now). |
| `create_VENDOR_part.py` | Recorded-journal COTS flow driven by the **McMaster scraper**: prompt for a part number → scrape JSON + download CAD → derive attributes → prompt for part name → create the part. |
| `create_VENDOR_part_dialog.dlx` | 5-field COTS dialog (Part Number, Part Name, Description, Manufacturer, Part Class). Used by `create_COTS_part.py`. Hand-authored; not yet round-tripped through Block UI Styler. |
| `create_VENDOR_partno_dialog.dlx` | Single-field "Part Number" dialog (block id `partNo`) — step 1 of `create_VENDOR_part.py`. |
| `create_VENDOR_partname_dialog.dlx` | Single-field "Part Name" dialog (block id `partName`) — step 4 of `create_VENDOR_part.py`, prefilled with the description. Sets `DB_PART_NAME`. |
| `scraper/` | Vendored copy of the McMaster-Carr scraper (`br435t/McMaster-scraper`). See `scraper/VENDORED.md`. Run as a subprocess, not imported into NX. |
| `nx_input.py` | Reusable UF `ask_string` text-prompt helper (legacy; no longer used but kept for reuse). |
| `new_part.py` | The original recorded journal (File → New → Item) this work was reverse-engineered from. Reference only. **Generated from inside NX** via **Tools → Journal → Record**, not hand-written. |
| `import_Parasolid.py` | Recorded journal (File → Import → Parasolid) that the `import_parasolid()` helper in `create_VENDOR_part.py` was derived from. Reference only. |
| `journal_create_vendorpart.py` | Fresh **working** recording of the COTS create (creates `ID.A/Name`). The source of truth for the required attributes and the `SetAddMaster(False)` fix. Reference only. |
| `.mcp.json` | Config for the `nxopen` MCP server. |

## COTS / vendor parts (`create_COTS_part.py`)

Creates a `BE9_COTS` item. Differs from the Design flow in three ways:

- **Item type** is `BE9_COTS` (not `BE9_Design`).
- **Part number is user-supplied** (the vendor/manufacturer PN), written as the
  `DB_PART_NO` attribute — *not* auto-assigned from a naming pattern.
- **Attributes span two categories:** `DB_PART_NO`/`DB_PART_NAME`/`DB_PART_DESC`
  on `BE9_COTS`; `HE_Manufacturer`/`Part Class` on `BE9_COTSRevision`.

Key functions: `create_part_cots(...)` (non-interactive creator),
`prompt_cots_attributes(...)` (BlockStyler dialog → dict of the 5 fields),
`scrape_mcmaster_part(...)` / `log_scraped_data(...)` (see below), and `main()`.

### `create_VENDOR_part.py` — scraper-driven COTS flow

This is the recorded journal wired to the scraper. `main()` does:

1. **Prompt for a part number** (`create_VENDOR_partno_dialog.dlx`).
2. **`fetch_mcmaster(pn)`** — subprocess to the external scraper: `scrape --out
   C:\TEMP\MCMASTER` (writes `<pn>.json`) then `cad --out C:\TEMP\MCMASTER
   --json` (downloads the default 3-D Parasolid, **no-threads** `*.X_T`).
3. **Derive attributes:** `part_no` = scraped `part_number`; `DB_PART_DESC` =
   `build_description()` = `title_primary` + `title_secondary`, concatenated and
   **UPPERCASED**; `HE_Manufacturer` = `"MCMASTER"`; `Part Class` = `"Class III"`.
4. **Prompt for the part name** (`create_VENDOR_partname_dialog.dlx`), prefilled
   with the description as an editable default → `DB_PART_NAME`.
5. Run the File → New → Item body to create the `BE9_COTS` part
   (`SetAddMaster(False)`, empty naming map, `DB_PART_NO` as an attribute — see
   gotcha #9).
6. **Import the downloaded Parasolid** (`import_parasolid()`) into the newly
   created work part — using the actual `*.X_T` path from step 2, guarded so it
   is skipped if the CAD download failed. Import happens after `Commit()`
   because the part must exist first.

Notes: a hard scrape failure aborts (the description depends on it); a CAD
download failure is logged but non-fatal (and the Parasolid import is skipped). Output dir is `C:\TEMP\MCMASTER`
(constant `MCMASTER_OUT`). Auto-login is left enabled, so an expired session
pops a sign-in window. The scraper side (`fetch_mcmaster`/`build_description`)
is live-tested; the dialogs + journal body still need a real NX run.

### McMaster scraper integration

`create_COTS_part.py` shells out to the vendored `scraper/mcmaster_scraper.py`
to fetch property data by part number. **It runs the scraper as a subprocess in
an external Python interpreter**, because the scraper needs Selenium + a real
Edge browser, which are not available in NX's embedded Python.

- Interpreter selection: `python_exe` arg → `MCMASTER_SCRAPER_PYTHON` env var →
  `python` on PATH. Point this at a venv that has selenium installed.
- Setup (once):
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\pip install -r scraper\requirements.txt
  $env:MCMASTER_SCRAPER_PYTHON = "C:\Code\Create-McMaster-Part\.venv\Scripts\python.exe"
  python scraper\mcmaster_scraper.py login   # cache the McMaster session
  ```
- **Current behavior: fetch & log only.** `main()` scrapes the entered part
  number and prints title/price/URL/specs to the Listing Window, but does *not*
  yet populate attributes from the scrape. `scrape_mcmaster_part()` never
  raises — failures return an `{"error": ...}` dict — so a scrape problem can't
  block part creation.
- **Not verified in a live NX session** (no selenium locally, and the scrape
  needs Edge + a McMaster login). The journal-side wiring (subprocess, JSON
  parsing, error paths, logging) is unit-tested.

## How to run

1. Open NX 2506 with a Teamcenter session active.
2. **File → Execute → NX Open…** → select `create_part.py`.
3. A "Create Part" dialog appears with **Name** and **Description** fields.
4. Fill them in, click **OK**. The part is created as a `BE9_Design` item with an
   auto-assigned part number; results are logged to the Listing Window
   (e.g. `Created part: 1135393-001.01/test name`).

## Key functions (`create_part.py`)

- `create_part_teamcenter(part_name, description, part_class="Class III", ...)`
  — the managed-mode creator. Sets up the template, the
  `PDM.PartOperationCreateBuilder`, auto-numbering, and attributes, then commits.
  Non-interactive, so it's reusable from other scripts.
- `prompt_name_and_description(dlx_path=...)` — launches the BlockStyler dialog and
  returns `(name, description)`; `(None, None)` on cancel.
- `list_templates()` — returns `(name, units, is_blank)` for all registered
  templates. Use to discover valid `@DB/...` template refs.
- `create_part(new_file_name, ...)` — native/filesystem-mode creator. **Does not
  work in this Teamcenter session** (template doesn't exist); kept for non-managed use.
- `main()` — prompts, then calls `create_part_teamcenter`.

## Gotchas discovered (hard-won — don't re-learn these)

1. **Managed vs native mode.** In Teamcenter mode you must drive creation through
   `theSession.PdmSession.CreateCreateOperationBuilder(...)` →
   `PDM.PartOperationCreateBuilder`. A plain `FileNew.Commit()` (native path) fails
   with "The selected template doesn't exist".
2. **Template ref format:** `@DB/<template>/<rev>`, e.g. `@DB/model-plain-1-inch-template/A`.
3. **`FileNew.UsesMasterModel` is a string** (`"No"`/`"Yes"`), not a bool.
4. **Explicit subpackage imports:** `import NXOpen` does not pull in subpackages —
   need `import NXOpen.PDM`, `import NXOpen.BlockStyler`, etc.
5. **Destination folder** comes from `theSession.PdmSession.GetUserName()` — don't
   hardcode the user.
6. **UF `AskStringInput` is a trap** (this is why we moved to BlockStyler):
   - Its `str` arg is a **ref buffer** that must be exactly **133 chars**
     (`" " * 133`); `""` returns empty regardless of input.
   - It needs `Ui.LockUgAccess(UF_UI_FROM_CUSTOM)` / `UnlockUgAccess` around it or
     no dialog appears.
   - Its `cue` shows in the **status/cue line**, never inside the box.
7. **BlockStyler dialogs require callbacks** registered before `Show()`, or NX
   raises "The Initialize callback is not registered in automation code". Register
   `AddInitializeHandler`, `AddUpdateHandler` (cb takes a `block` arg, returns 0),
   `AddOkHandler`, `AddApplyHandler`. Read block values **inside** the OK/Apply
   callback, not after `Show()`.
8. The `.dlx` was hand-built from NX's own sample
   `C:\SPLM\NX\NX2506\MACH\auxiliary\sme\setLicense.dlx` to guarantee a valid schema.
9. **`SetAddMaster(False)` is required for the COTS commit.** A fresh working
   recording (`journal_create_vendorpart.py`, creates `ID.A/Name`) revealed the
   real fix for `Commit()` failing with "The new filename is not a valid file
   specification": call
   `partOperationCreateBuilder.SetAddMaster(False)` before creating the COTS
   logical objects. Dead ends ruled out along the way:
   - `FileNew.NewFileName` is **not** it — setting it to a bare id throws
     "not a valid file specification" on assignment; managed mode never sets it.
   - A quoted-literal naming pattern is **not** it either. The working recording
     uses an **empty** naming map and sets `DB_PART_NO` as a plain attribute
     (`CreateAttributeTitleToNamingPatternMap([], [])` + `DB_PART_NO` via
     `AttributePropertiesBuilder`), and commits fine once `SetAddMaster(False)`
     is present.
   Required attributes (all present in `create_VENDOR_part.py`): `DB_PART_NO`,
   `DB_PART_NAME`, `DB_PART_DESC` (category `BE9_COTS`); `HE_Manufacturer`,
   `Part Class` (category `BE9_COTSRevision`).

## Status / open items

- Prompt flow (BlockStyler dialog) and Teamcenter creation are wired up end to end.
- **Verify in NX:** confirm the dialog loads and the part is created; the `.dlx`
  was authored by hand and hasn't been round-tripped through Block UI Styler.
- The created part is not explicitly **saved to Teamcenter** after `Commit()` (the
  recorded journal didn't either). If a DB save is needed, add it.
- `part_class` is fixed at `"Class III"` — make it a dialog field if it should vary.
- **COTS flow:** the scraper is wired for **log-only**. Next step (when ready) is
  to map scraped fields onto attributes (e.g. title → `DB_PART_NAME`, secondary/
  specs → `DB_PART_DESC`, `HE_Manufacturer` → `McMaster-Carr`) and optionally
  write each spec as its own NX user attribute.
- **COTS dialog `.dlx`** is hand-authored and not yet verified to load in NX.
- If `Part Class` should be a fixed list (Class I/II/III), change the
  `partClass` block in `create_VENDOR_part_dialog.dlx` to a Combo.
