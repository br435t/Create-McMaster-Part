# NX 2506
# Journal created by br435t on Tue Jul 14 09:12:10 2026 Pacific Daylight Time
#
import json
import os
import subprocess
import sys
import NXOpen
import NXOpen.PDM
import NXOpen.BlockStyler

_HERE = os.path.dirname(os.path.abspath(__file__))

# Single-field BlockStyler dialogs (generated to match create_part_dialog.dlx).
_PARTNO_DLX = os.path.join(_HERE, "create_VENDOR_partno_dialog.dlx")
_PARTNAME_DLX = os.path.join(_HERE, "create_VENDOR_partname_dialog.dlx")

# Vendored McMaster scraper + where its output lands.
_SCRAPER_SCRIPT = os.path.join(_HERE, "scraper", "mcmaster_scraper.py")
MCMASTER_OUT = r"C:\TEMP\MCMASTER"


def prompt_string(dlx_path, block_id, default=None):
    """Show a single-field string BlockStyler dialog and return its value.

    Returns the stripped field value, or None if the user cancels. If `default`
    is given it is pre-filled into the field (editable by the user).

    BlockStyler dialogs require callback handlers to be registered (NX errors
    with "The Initialize callback is not registered" otherwise), and block
    values must be read inside the OK/Apply callback.
    """
    the_ui = NXOpen.UI.GetUI()
    dialog = the_ui.CreateDialog(dlx_path)
    captured = {}

    def initialize_cb():
        if default:
            props = dialog.GetBlockProperties(block_id)
            # Set both storages: a KeyIn field reads "Value", a Wide field
            # reads "WideValue". Best-effort — never block the dialog.
            for key in ("Value", "WideValue"):
                try:
                    props.SetString(key, default)
                except Exception:
                    pass

    def update_cb(block):
        return 0

    def apply_cb():
        props = dialog.GetBlockProperties(block_id)
        value = ""
        for key in ("Value", "WideValue"):
            try:
                candidate = props.GetString(key)
            except Exception:
                candidate = ""
            if candidate:
                value = candidate
                break
        captured["value"] = value
        return 0

    def ok_cb():
        apply_cb()

    dialog.AddInitializeHandler(initialize_cb)
    dialog.AddUpdateHandler(update_cb)
    dialog.AddOkHandler(ok_cb)
    dialog.AddApplyHandler(apply_cb)

    try:
        response = dialog.Show()
        if response != NXOpen.Selection.Response.Ok:
            return None
        return (captured.get("value") or "").strip()
    finally:
        dialog.Dispose()


def _scraper_python():
    """External Python that has selenium installed (see scraper/VENDORED.md).

    Preference order (so it works even when NX didn't inherit the env var):
      1. MCMASTER_SCRAPER_PYTHON environment variable
      2. the repo-local venv next to this script (.venv\\Scripts\\python.exe)
      3. "python" on PATH
    """
    env = os.environ.get("MCMASTER_SCRAPER_PYTHON")
    if env:
        return env
    venv_py = os.path.join(_HERE, ".venv", "Scripts", "python.exe")
    if os.path.exists(venv_py):
        return venv_py
    return "python"


def _run_scraper(sub_args, timeout=300):
    cmd = [_scraper_python(), _SCRAPER_SCRIPT] + sub_args
    return subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        universal_newlines=True, timeout=timeout)


def fetch_mcmaster(part_no, out_dir=MCMASTER_OUT):
    """Scrape property data (JSON) and download the no-threads Parasolid CAD.

    Runs the vendored scraper in an external interpreter as a subprocess:
      1. `scrape <pn> --out <dir>`  -> writes <dir>/<pn>.json
      2. `cad <pn> --out <dir> --json` -> downloads the default 3-D Parasolid,
         no-threads *.X_T into <dir>

    Returns a dict:
      {"data": <scraped dict or None>, "json_file": path or None,
       "cad_file": path or None, "error": <hard error or None>,
       "cad_error": <soft CAD error or None>}
    A hard `error` means the JSON (and thus the description) is unavailable;
    `cad_error` is non-fatal. Never raises.
    """
    result = {"data": None, "json_file": None, "cad_file": None,
              "error": None, "cad_error": None}  # type: dict
    try:
        os.makedirs(out_dir, exist_ok=True)
    except OSError as ex:
        result["error"] = "cannot create {0}: {1}".format(out_dir, ex)
        return result

    # 1. Scrape structured data to <out_dir>/<part_no>.json
    try:
        proc = _run_scraper(["scrape", part_no, "--out", out_dir])
    except (OSError, subprocess.SubprocessError) as ex:
        result["error"] = "failed to run scraper: {0}".format(ex)
        return result
    if proc.returncode != 0:
        result["error"] = "scrape exited {0}: {1}".format(
            proc.returncode, (proc.stderr or "").strip())
        return result

    json_file = os.path.join(out_dir, part_no + ".json")
    if not os.path.exists(json_file):
        result["error"] = "scrape produced no JSON at {0}".format(json_file)
        return result
    try:
        with open(json_file, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError) as ex:
        result["error"] = "cannot read scraped JSON: {0}".format(ex)
        return result
    result["json_file"] = json_file
    result["data"] = data
    if data.get("error"):
        result["error"] = "scrape error: {0}".format(data["error"])
        return result

    # 2. Download the CAD (default = 3-D Parasolid, no threads, *.X_T)
    try:
        cad_proc = _run_scraper(["cad", part_no, "--out", out_dir, "--json"])
    except (OSError, subprocess.SubprocessError) as ex:
        result["cad_error"] = "failed to run CAD download: {0}".format(ex)
        return result
    if cad_proc.returncode == 0:
        try:
            result["cad_file"] = json.loads(cad_proc.stdout).get("file")
        except ValueError:
            result["cad_error"] = "could not parse CAD output"
    else:
        result["cad_error"] = "CAD download exited {0}: {1}".format(
            cad_proc.returncode, (cad_proc.stderr or "").strip())
    return result


def build_description(data):
    """part_desc = title_primary + title_secondary, concatenated and UPPERCASED."""
    primary = (data.get("title_primary") or "").strip()
    secondary = (data.get("title_secondary") or "").strip()
    return " ".join(p for p in (primary, secondary) if p).upper()


def import_parasolid(the_session, input_file, curves=True, surfaces=True, solids=True):
    """Import a Parasolid (*.x_t) file into the current work part.

    Mirrors the recorded File > Import > Parasolid flow (see import_Parasolid.py).
    """
    importer = the_session.DexManager.CreateParasolidImporter()
    try:
        importer.ObjectTypes.Curves = curves
        importer.ObjectTypes.Surfaces = surfaces
        importer.ObjectTypes.Solids = solids
        importer.SetMode(NXOpen.BaseImporter.Mode.NativeFileSystem)
        importer.InputFile = input_file
        importer.Commit()
    finally:
        importer.Destroy()


def main(args) :

    theSession  = NXOpen.Session.GetSession() #type: NXOpen.Session
    workPart = theSession.Parts.Work
    displayPart = theSession.Parts.Display
    lw = theSession.ListingWindow
    lw.Open()

    # --- 1. Ask for the McMaster part number ---
    entered_pn = prompt_string(_PARTNO_DLX, "partNo")
    if entered_pn is None:
        lw.WriteLine("Cancelled: part number dialog dismissed.")
        return
    if not entered_pn:
        lw.WriteLine("Cancelled: no part number entered.")
        return

    # --- 2. Scrape JSON + download the no-threads Parasolid CAD ---
    lw.WriteLine("Fetching McMaster data for {0} -> {1} ...".format(
        entered_pn, MCMASTER_OUT))
    fetched = fetch_mcmaster(entered_pn)
    if fetched["error"]:
        lw.WriteLine("Aborted: {0}".format(fetched["error"]))
        return
    data = fetched["data"]
    if fetched.get("json_file"):
        lw.WriteLine("  JSON: {0}".format(fetched["json_file"]))
    if fetched.get("cad_file"):
        lw.WriteLine("  CAD : {0}".format(fetched["cad_file"]))
    elif fetched.get("cad_error"):
        lw.WriteLine("  CAD download warning: {0}".format(fetched["cad_error"]))

    # --- 3. Derive attribute values ---
    part_no = (data.get("part_number") or entered_pn).strip()
    part_desc = build_description(data)          # title_primary + secondary, UPPER
    manufacturer = "MCMASTER"                    # hardcoded
    part_class = "Class III"                     # hardcoded
    lw.WriteLine("  Description: {0}".format(part_desc))

    # --- 4. Ask for the part name (pre-filled with the description, all caps) ---
    part_name = prompt_string(_PARTNAME_DLX, "partName", default=part_desc)
    if part_name is None:
        lw.WriteLine("Cancelled: part name dialog dismissed.")
        return
    if not part_name:
        lw.WriteLine("Cancelled: no part name entered.")
        return

    lw.WriteLine("Creating COTS part {0} ...".format(part_no))
    # --- 5. Create the BE9_COTS item (File > New > Item) ---
    fileNew = theSession.Parts.FileNew()
    fileNew.TemplateFileName = "@DB/model-plain-1-inch-template/A"
    fileNew.UseBlankTemplate = False
    fileNew.ApplicationName = "ModelTemplate"
    fileNew.Units = NXOpen.Part.Units.Inches
    fileNew.RelationType = "master"
    fileNew.UsesMasterModel = "No"                 # NOTE: string, not bool
    fileNew.TemplateType = NXOpen.FileNewTemplateType.Item
    fileNew.TemplatePresentationName = "Model"
    fileNew.ItemType = "BE9_Design,BE9_Electrical,BE9_COTS,BE9_Tooling"
    fileNew.Specialization = ""
    fileNew.SetCanCreateAltrep(False)

    opBuilder = theSession.PdmSession.CreateCreateOperationBuilder(
        NXOpen.PDM.PartOperationBuilder.OperationType.Create)
    fileNew.SetPartOperationCreateBuilder(opBuilder)
    opBuilder.SetOperationSubType(
        NXOpen.PDM.PartOperationCreateBuilder.OperationSubType.FromTemplate)
    opBuilder.SetModelType("master")
    opBuilder.SetItemType("BE9_COTS")
    opBuilder.DefaultDestinationFolder = "br435t"

    logicalObjects = opBuilder.CreateLogicalObjects()
    sourceObjects = logicalObjects[0].GetUserAttributeSourceObjects()

    # COTS parts are not auto-numbered; register an empty naming map so the
    # part number comes from the DB_PART_NO attribute set below.
    namingMap = opBuilder.CreateAttributeTitleToNamingPatternMap([], [])
    errorList = opBuilder.AutoAssignAttributesWithNamingPattern(
        [logicalObjects[0]], [namingMap])
    errorList.Dispose()

    attrBuilder = theSession.AttributeManager.CreateAttributePropertiesBuilder(
        NXOpen.BasePart.Null, [],
        NXOpen.AttributePropertiesBuilder.OperationType.Create)
    attrBuilder.SetAttributeObjects([sourceObjects[0]])

    # Item-level attributes (category BE9_COTS).
    attrBuilder.Category = "BE9_COTS"
    attrBuilder.Title = "DB_PART_NO"
    attrBuilder.StringValue = part_no
    attrBuilder.CreateAttribute()

    attrBuilder.Title = "DB_PART_NAME"
    attrBuilder.StringValue = part_name
    attrBuilder.CreateAttribute()

    attrBuilder.Title = "DB_PART_DESC"
    attrBuilder.StringValue = part_desc
    attrBuilder.CreateAttribute()

    # Revision-level attributes (category BE9_COTSRevision).
    attrBuilder.Category = "BE9_COTSRevision"
    attrBuilder.Title = "HE_Manufacturer"
    attrBuilder.StringValue = manufacturer
    attrBuilder.CreateAttribute()

    attrBuilder.Title = "Part Class"
    attrBuilder.StringValue = part_class
    attrBuilder.CreateAttribute()

    # Finalize and commit.
    fileNew.MasterFileName = ""
    fileNew.MakeDisplayedPart = True
    fileNew.DisplayPartOption = NXOpen.DisplayPartOption.AllowAdditional
    opBuilder.ValidateLogicalObjectsToCommit()
    opBuilder.CreateSpecificationsForLogicalObjects([logicalObjects[0]])
    fileNew.Commit()

    workPart = theSession.Parts.Work
    displayPart = theSession.Parts.Display
    lw.WriteLine("Created COTS part: {0}".format(workPart.Leaf))

    fileNew.Destroy()
    attrBuilder.Destroy()

    # --- 6. Import the downloaded Parasolid geometry into the new part ---
    cad_file = fetched.get("cad_file")
    if cad_file and os.path.exists(cad_file):
        lw.WriteLine("Importing Parasolid: {0}".format(cad_file))
        import_parasolid(theSession, cad_file)
        lw.WriteLine("Imported geometry into {0}.".format(workPart.Leaf))
    else:
        lw.WriteLine("No CAD file available; skipped Parasolid import.")

    theSession.CleanUpFacetedFacesAndEdges()


if __name__ == '__main__':
    main(sys.argv[1:])
