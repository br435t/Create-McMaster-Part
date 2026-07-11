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
| `create_part.py` | Main script. Prompts (BlockStyler dialog), then creates the part. |
| `create_part_dialog.dlx` | BlockStyler dialog layout (Name + Description fields). Must sit next to `create_part.py`. |
| `nx_input.py` | Reusable UF `ask_string` text-prompt helper (legacy; no longer used by `create_part.py` but kept for reuse). |
| `new_part.py` | The original recorded journal (File → New → Item) this work was reverse-engineered from. Reference only. **Generated from inside NX** via **Tools → Journal → Record**, not hand-written. |
| `.mcp.json` | Config for the `nxopen` MCP server. |

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

## Status / open items

- Prompt flow (BlockStyler dialog) and Teamcenter creation are wired up end to end.
- **Verify in NX:** confirm the dialog loads and the part is created; the `.dlx`
  was authored by hand and hasn't been round-tripped through Block UI Styler.
- The created part is not explicitly **saved to Teamcenter** after `Commit()` (the
  recorded journal didn't either). If a DB save is needed, add it.
- `part_class` is fixed at `"Class III"` — make it a dialog field if it should vary.
