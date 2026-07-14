# Create McMaster Part (NX Open)

NX Open (Python) automation for **NX 2506** in **Teamcenter managed mode**. Enter
a McMaster-Carr part number and it scrapes the product data, downloads the CAD,
creates a `BE9_COTS` part in Teamcenter, and imports the geometry — prompting
through BlockStyler dialogs along the way.

There are two entry points:

- **`create_VENDOR_part.py`** — the McMaster/COTS flow (part number → scrape →
  create → import). This is the main tool.
- **`create_part.py`** — the original Design-part flow (prompt for Name +
  Description, auto-assigned number). Kept for reference/reuse.

## Prerequisites

- **NX 2506** with an active **Teamcenter** session (managed mode).
- **Microsoft Edge** (pre-installed on Windows 10/11) — the scraper drives it.
- **Python 3.10+** on the machine (for the scraper). Get it from
  <https://www.python.org/downloads/> and tick *"Add python.exe to PATH"*.

## One-click setup

1. Download or clone this repo to a folder, e.g. `C:\Code\Create-McMaster-Part`.
2. **Double-click `setup.bat`.**

That creates the Python virtual environment the scraper needs, installs its
dependencies (works behind the corporate SSL proxy via `pip-system-certs`), and
opens a browser so you can log in to McMaster once. Re-running it is safe.

> `setup.bat` puts the environment in `.venv` next to the scripts, and
> `create_VENDOR_part.py` finds it automatically — no environment variables to
> set. Pass `nologin` (`setup.bat nologin`) to skip the McMaster login step.

## Create a part

1. Open **NX 2506** with a Teamcenter session.
2. **File → Execute → NX Open…** → select **`create_VENDOR_part.py`**.
3. Enter the **McMaster part number** when prompted.
4. The tool scrapes the product data, downloads the no-threads Parasolid CAD to
   `C:\TEMP\MCMASTER`, and shows a **Part Name** dialog pre-filled with the
   description (edit if you like).
5. It creates the `BE9_COTS` part, sets its attributes, and imports the CAD.
   Progress is written to the **Listing Window**.

Attributes set: `DB_PART_NO` = part number, `DB_PART_NAME` = the name you
confirm, `DB_PART_DESC` = product title (all caps), `HE_Manufacturer` =
`MCMASTER`, `Part Class` = `Class III`.

Keep each script next to its `.dlx` dialog file(s) and the `scraper/` folder —
paths are resolved relative to the script.

## Files

| File | Purpose |
|------|---------|
| `setup.bat` | One-click setup: venv + dependencies + McMaster login. |
| `create_VENDOR_part.py` | Main flow: part number → scrape → create COTS part → import CAD. |
| `create_VENDOR_partno_dialog.dlx` / `create_VENDOR_partname_dialog.dlx` | Part-number and part-name dialogs. |
| `create_COTS_part.py` | Reusable COTS-part module (scrape is log-only). |
| `create_part.py` + `create_part_dialog.dlx` | Original Design-part flow. |
| `scraper/` | Vendored McMaster-Carr scraper (Selenium). See `scraper/VENDORED.md`. |
| `import_Parasolid.py`, `new_part.py`, `nx_input.py` | Recorded-journal / helper references. |
| `HANDOFF.md` | Deeper notes: key functions, gotchas, open items. |

## Notes

- Targets **Teamcenter managed mode**; the native `create_part` helper won't
  work in a managed session.
- The scraper needs a McMaster login (cached in a dedicated Edge profile). If the
  session expires, the tool opens a sign-in window automatically.
- See `HANDOFF.md` for the full list of NX Open / Teamcenter gotchas.
