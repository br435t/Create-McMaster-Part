# Helion NX Tools

NX Open (Python) automation and supporting tools for **NX 2506** running in
**Teamcenter managed mode** at Helion.

The repo is organized by **where the code runs** — inside NX, outside NX, or
recorded from NX as reference.

## Repository structure

```
Helion-NX-Tools/
├── NX-Scripts/                  Scripts run INSIDE NX (File → Execute → NX Open…)
│   └── Create-McMaster-Part/    McMaster-Carr COTS part creator (+ its .dlx dialogs)
│       └── README.md            How to set up and run the Create-McMaster-Part tool
├── Tools/                       External code run OUTSIDE NX (as a subprocess)
│   └── scraper/                 McMaster-Carr Selenium scraper (vendored)
├── example_journals/            Journals RECORDED in NX, kept as reference only
├── setup.bat                    One-click setup: .venv + dependencies + McMaster login
├── requirements.txt             Python deps for the Tools (installed by setup.bat)
├── .venv/                       Python virtual environment (git-ignored)
├── HANDOFF.md                   Deep notes: key functions, gotchas, open items
└── README.md                    This file
```

## What lives where

| Folder | Runs | Contents |
|--------|------|----------|
| [NX-Scripts/](NX-Scripts/) | Inside NX (File → Execute → NX Open…) | The tools NX operators actually run, each in its own folder alongside its `.dlx` BlockStyler dialogs. |
| [Tools/](Tools/) | Outside NX (subprocess, real Python) | Support code NX's embedded Python can't run — e.g. the Selenium scraper, which needs a real Edge browser. |
| [example_journals/](example_journals/) | Not executed | Journals recorded via Tools → Journal → Record, kept for reverse-engineering NX Open calls. |

An NX script locates the repo root by walking up the folder tree, so it finds
`Tools/` and `.venv/` no matter how deep it sits under `NX-Scripts/`.

## Tools

- **[Create McMaster Part](NX-Scripts/Create-McMaster-Part/README.md)** — enter a
  McMaster-Carr part number; it scrapes the product data, downloads the CAD,
  creates a `BE9_COTS` part in Teamcenter, and imports the geometry. See its
  [README](NX-Scripts/Create-McMaster-Part/README.md) for setup and usage.

## Getting started

1. Clone this repo to a local folder, e.g. `C:\Code\Helion-NX-Tools`.
2. **Double-click** [setup.bat](setup.bat) — creates `.venv`, installs
   dependencies (behind the corporate SSL proxy), and caches the McMaster login.
3. Follow the per-tool README under [NX-Scripts/](NX-Scripts/) to run a tool.

## More detail

See [HANDOFF.md](HANDOFF.md) for the full list of NX Open / Teamcenter gotchas,
key functions, and open items.
