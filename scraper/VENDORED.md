# Vendored code

The files in this folder are a vendored copy of the **McMaster-Carr scraper**.

- **Source:** https://github.com/br435t/McMaster-scraper
- **Commit:** `442c62dd4b4db271f5db2bc811048cafaa27490e`
- **Vendored on:** 2026-07-14

Only the functional files were copied (`mcmaster_scraper.py`, `requirements.txt`)
plus its docs (`README.md`, `HANDOFF.md`). The `examples/` folder (including a
large binary `.X_T` CAD sample) was not vendored.

`create_COTS_part.py` invokes `mcmaster_scraper.py` as a **subprocess** using an
external Python interpreter that has Selenium installed (see
`scrape_mcmaster_part()` in that module). It is not imported into NX's embedded
interpreter.

To update this copy, re-pull from the source repo and refresh the commit hash above.
