# Handoff — NX Open "Create Part" automation

Automates creating a McMaster-Carr COTS part in **NX 2506** running in
**Teamcenter managed mode**: enter a part number, scrape its data + CAD, and
create the `BE9_COTS` item with the imported geometry.

## Environment

- **NX 2506**, Python (CPython) journals run via **File → Execute → NX Open…**.
- Runs in **Teamcenter managed mode** (not native/filesystem mode). This changes
  everything about how parts are created (see gotchas).
- Custom Helion item types: `BE9_Design, BE9_Electrical, BE9_COTS, BE9_Tooling`
  (the part is created as `BE9_COTS`).
- Default template: `@DB/model-plain-1-inch-template/A` (units = inches).
- An `nxopen` MCP server (see `.mcp.json`) indexes the NX 2506 Python API and
  stubs — use it to look up signatures. **Note:** it does **not** index
  `NXOpen.UF` (that subsystem has no stubs on disk).

## Repository layout

Organized by where the code runs:

- **`NX-Scripts/`** — scripts executed **inside NX** (File → Execute → NX Open…).
- **`Tools/`** — external support code run **outside NX** as a subprocess
  (scrapers, shared logic, future tools).
- **`example_journals/`** — journals **recorded in NX** (Tools → Journal →
  Record), kept as reference for reverse-engineering NX Open calls. Not run
  directly.
- **Repo root** — `setup.bat`, `requirements.txt`, `.venv/` (git-ignored), and
  the docs.

An NX script finds the repo root by walking up, so it locates `Tools/` and
`.venv/` no matter how deep it sits under `NX-Scripts/`.

### Files

| Path | Purpose |
|------|---------|
| `NX-Scripts/Create-McMaster-Part/create_VENDOR_part.py` | **Main tool.** Scraper-driven COTS flow: prompt for a part number → scrape JSON + download CAD → derive attributes → prompt for part name → create the `BE9_COTS` part → import the CAD. |
| `NX-Scripts/Create-McMaster-Part/create_VENDOR_partno_dialog.dlx` | Single-field "Part Number" dialog (block id `partNo`) — step 1. |
| `NX-Scripts/Create-McMaster-Part/create_VENDOR_partname_dialog.dlx` | Single-field "Part Name" dialog (block id `partName`) — prefilled with the description; sets `DB_PART_NAME`. |
| `NX-Scripts/Create-McMaster-Part/create_VENDOR_part_dialog.dlx` | Legacy 5-field COTS dialog. Not used by the current flow; kept for reference. |
| `Tools/scraper/` | Vendored copy of the McMaster-Carr scraper (`br435t/McMaster-scraper`). See `Tools/scraper/VENDORED.md`. Run as a subprocess, not imported into NX. |
| `example_journals/journal_create_vendor_part.py` | Fresh **working** recording of the COTS create (creates `ID.A/Name`). Source of truth for the required attributes and the `SetAddMaster(False)` fix. |
| `example_journals/journal_import_Parasolid.py` | Recorded File → Import → Parasolid journal the `import_parasolid()` helper was derived from. |
| `.mcp.json` | Config for the `nxopen` MCP server (git-ignored). |

## COTS / vendor parts (`create_VENDOR_part.py`)

Creates a `BE9_COTS` item. Differs from the Design flow in three ways:

- **Item type** is `BE9_COTS` (not `BE9_Design`).
- **Part number is user-supplied** (the vendor/manufacturer PN), written as the
  `DB_PART_NO` attribute — *not* auto-assigned from a naming pattern.
- **Attributes span two categories:** `DB_PART_NO`/`DB_PART_NAME`/`DB_PART_DESC`
  on `BE9_COTS`; `HE_Manufacturer`/`Part Class` on `BE9_COTSRevision`.

### Flow (`main()`)

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

`create_VENDOR_part.py` shells out to the vendored `Tools/scraper/mcmaster_scraper.py`
to fetch property data by part number. **It runs the scraper as a subprocess in
an external Python interpreter**, because the scraper needs Selenium + a real
Edge browser, which are not available in NX's embedded Python.

- Interpreter selection (`_scraper_python()`): `MCMASTER_SCRAPER_PYTHON` env var
  → the repo-root `.venv` (found by walking up from the script) → `python` on
  PATH. No env var needed if `.venv` exists — the script auto-detects it.
- Setup (once): run `setup.bat` at the repo root (creates `.venv`, installs
  `requirements.txt` behind the corporate proxy, and runs the
  McMaster `login` to cache the session).
- `fetch_mcmaster()` returns a dict with `data` / `json_file` / `cad_file` and
  `error` / `cad_error`; it never raises. A hard scrape error aborts creation
  (the description depends on it); a CAD-download error is non-fatal (the
  Parasolid import is just skipped).

## How to run

1. One-time setup: run `setup.bat` at the repo root (creates `.venv`, installs
   `requirements.txt`, and caches the McMaster login).
2. Open NX 2506 with a Teamcenter session active.
3. **File → Execute → NX Open…** → select
   `NX-Scripts/Create-McMaster-Part/create_VENDOR_part.py`.
4. Enter the McMaster part number. The tool scrapes the data, downloads the CAD,
   prompts for the part name, creates the `BE9_COTS` part, and imports the CAD;
   progress is logged to the Listing Window.

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
   recording (`example_journals/journal_create_vendor_part.py`, creates
   `ID.A/Name`) revealed the
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
