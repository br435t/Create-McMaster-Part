# NX Open — Create Part

NX Open (Python) automation that creates a new part in **NX 2506** running in
**Teamcenter managed mode**, prompting the user for a **Name** and **Description**
through a BlockStyler dialog.

## Requirements

- Siemens **NX 2506** with an active **Teamcenter** session (managed mode).
- Runs as a Python journal — no extra install.

## Usage

1. In NX: **File → Execute → NX Open…**
2. Select `create_part.py`.
3. In the **Create Part** dialog, enter a Name and Description, then click **OK**.
4. The part is created as a `BE9_Design` item with an auto-assigned part number.
   The result is logged to the Listing Window, e.g.
   `Created part: 1135393-001.01/test name`.

Keep `create_part.py` and `create_part_dialog.dlx` in the **same folder** — the
script loads the dialog relative to itself.

## Files

| File | Purpose |
|------|---------|
| `create_part.py` | Main script: prompt for name/description, then create the part. |
| `create_part_dialog.dlx` | BlockStyler dialog layout (Name + Description fields). |
| `nx_input.py` | Reusable UF `ask_string` text-prompt helper (kept for reuse). |
| `new_part.py` | Original recorded journal used as the reference for the Teamcenter workflow. |
| `.mcp.json` | Config for the `nxopen` MCP server (NX 2506 Python API reference). |
| `HANDOFF.md` | Deeper notes: key functions, gotchas, and open items. |

> **Note:** `new_part.py` was **generated from inside NX** by recording a journal
> (**Tools → Journal → Record**) while creating a part through **File → New → Item**.
> It is not hand-written — it's the machine-recorded reference this automation was
> reverse-engineered from. You can record similar journals the same way to
> reverse-engineer other NX workflows.

## Notes

- This targets **Teamcenter managed mode**. The native/filesystem `create_part`
  helper in `create_part.py` will not work in a managed session.
- Default template is `@DB/model-plain-1-inch-template/A` (inches).
- See `HANDOFF.md` for the full list of NX Open gotchas discovered while building this.
