"""create_COTS_part.py

Reusable helper for creating a new COTS ("commercial off-the-shelf" / vendor)
part in NX with NX Open (Python), in Teamcenter managed mode.

Tested against the Siemens NX 2506 NXOpen Python API.

This mirrors the structure of create_part.py, but targets the BE9_COTS item
type instead of BE9_Design. The important differences from a Design part:

  * Item type is ``BE9_COTS`` (not ``BE9_Design``).
  * The part number is **entered by the user** (the vendor / manufacturer part
    number), not auto-assigned from a naming pattern.
  * Attributes are split across two categories:
      - ``BE9_COTS``          : DB_PART_NO, DB_PART_NAME, DB_PART_DESC
      - ``BE9_COTSRevision``  : HE_Manufacturer, Part Class

Run inside NX (File > Execute > NX Open...) and it will prompt for the vendor
fields via the BlockStyler dialog, or import and call directly:

    from create_COTS_part import create_part_cots
    part = create_part_cots(
        part_no="91251A537",
        part_name="Socket Head Screw",
        description="1/4-20 x 1in, alloy steel",
        manufacturer="McMaster-Carr",
    )
"""

import json
import os
import subprocess

import NXOpen
import NXOpen.PDM
import NXOpen.BlockStyler

# --- Vendored McMaster-Carr scraper (see scraper/VENDORED.md) --------------- #
# The scraper drives a headless Edge browser via Selenium, which is NOT
# available in NX's embedded Python. We therefore run it as a SUBPROCESS in an
# external interpreter that has selenium installed, and parse its JSON output.
_SCRAPER_SCRIPT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "scraper", "mcmaster_scraper.py")


def scrape_mcmaster_part(part_no, python_exe=None, timeout=300, extra_args=None):
    """Scrape McMaster-Carr property data for a part number.

    Runs the vendored scraper/mcmaster_scraper.py in an EXTERNAL Python
    interpreter (the one with Selenium/Edge installed) via subprocess and
    returns the parsed JSON dict. NX's embedded interpreter is not used for the
    scrape itself.

    Args:
        part_no:     McMaster part number, e.g. "91274A004".
        python_exe:  Path to the Python that has selenium installed. Defaults to
                     the MCMASTER_SCRAPER_PYTHON environment variable, or
                     "python" on PATH.
        timeout:     Seconds to wait for the scrape (browser + login can be slow).
        extra_args:  Extra CLI args to pass to the scraper (e.g. ["--headful"]).

    Returns:
        The scraped dict. On any failure (or a McMaster error) the dict carries
        an "error" key rather than raising, so the caller can log and continue.
    """
    if python_exe is None:
        python_exe = os.environ.get("MCMASTER_SCRAPER_PYTHON", "python")

    cmd = [python_exe, _SCRAPER_SCRIPT, "scrape", part_no, "--stdout"]
    if extra_args:
        cmd.extend(extra_args)

    try:
        proc = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError) as ex:
        return {"part_number": part_no,
                "error": "failed to run scraper: {0}".format(ex)}

    if proc.returncode != 0:
        return {"part_number": part_no,
                "error": "scraper exited {0}: {1}".format(
                    proc.returncode, (proc.stderr or "").strip())}

    try:
        data = json.loads(proc.stdout)
    except ValueError as ex:
        return {"part_number": part_no,
                "error": "could not parse scraper output: {0}".format(ex),
                "raw": proc.stdout}

    # `scrape --stdout` returns a dict for one part, a list for several.
    if isinstance(data, list):
        data = data[0] if data else {"part_number": part_no, "error": "no data"}
    return data


def log_scraped_data(lw, data):
    """Write scraped McMaster property data to the NX Listing Window."""
    lw.WriteLine("--- McMaster property data ---")
    if data.get("error"):
        lw.WriteLine("  scrape error: {0}".format(data["error"]))
        return
    lw.WriteLine("  Part number : {0}".format(data.get("part_number")))
    lw.WriteLine("  Title       : {0}".format(
        data.get("title_primary") or data.get("title")))
    lw.WriteLine("  Detail      : {0}".format(data.get("title_secondary")))
    lw.WriteLine("  Price       : {0}".format(data.get("price")))
    lw.WriteLine("  URL         : {0}".format(data.get("url")))
    specs = data.get("specs") or []
    lw.WriteLine("  Specs ({0}):".format(len(specs)))
    for spec in specs:
        prefix = (spec.get("group") + " / ") if spec.get("group") else ""
        lw.WriteLine("    - {0}{1}: {2}".format(
            prefix, spec.get("label"), spec.get("value")))


def create_part_cots(
    part_no,
    part_name,
    description="",
    manufacturer="",
    part_class="Class III",
    item_type="BE9_COTS",
    revision_category="BE9_COTSRevision",
    destination_folder=None,
    template_file_name="@DB/model-plain-1-inch-template/A",
    template_presentation_name="Model",
    application_name="ModelTemplate",
    item_types="BE9_Design,BE9_Electrical,BE9_COTS,BE9_Tooling",
    units=NXOpen.Part.Units.Inches,
    make_displayed=True,
):
    """Create a new COTS/vendor part in Teamcenter (managed mode) from a template.

    Unlike a Design part, the part number is supplied by the caller (the vendor
    part number) rather than auto-assigned, and is written as the DB_PART_NO
    attribute alongside the other descriptive attributes.

    Args:
        part_no:                    Vendor/manufacturer part number. Written to
                                    the DB_PART_NO attribute (category = item_type).
        part_name:                  Value for the DB_PART_NAME attribute.
        description:                Value for the DB_PART_DESC attribute.
        manufacturer:               Value for the HE_Manufacturer attribute
                                    (category = revision_category).
        part_class:                 Value for the "Part Class" attribute
                                    (category = revision_category), e.g. "Class III".
        item_type:                  Item type created, e.g. "BE9_COTS". Also the
                                    attribute category for DB_PART_* attributes.
        revision_category:          Category for revision-level attributes
                                    (HE_Manufacturer, Part Class).
        destination_folder:         Teamcenter destination folder. Defaults to
                                    the logged-in Teamcenter user's home
                                    (PdmSession.GetUserName()) when None.
        template_file_name:         TC template ref, "@DB/<template>/<rev>".
        template_presentation_name: Template name as shown in File > New.
        application_name:           Application type, e.g. "ModelTemplate".
        item_types:                 Comma-separated item types the template
                                    supports (populates the type dropdown).
        units:                      NXOpen.Part.Units.Inches or .Millimeters.
        make_displayed:             Make the new part the displayed part.

    Returns:
        The newly created NXOpen.Part (the session's work part).
    """
    the_session = NXOpen.Session.GetSession()

    file_new = the_session.Parts.FileNew()
    op_builder = None
    attr_builder = None

    try:
        # --- Template selection (managed mode) ---
        file_new.TemplateFileName = template_file_name
        file_new.UseBlankTemplate = False
        file_new.ApplicationName = application_name
        file_new.Units = units
        file_new.RelationType = "master"
        file_new.UsesMasterModel = "No"          # NOTE: string, not bool
        file_new.TemplateType = NXOpen.FileNewTemplateType.Item
        file_new.TemplatePresentationName = template_presentation_name
        file_new.ItemType = item_types
        file_new.Specialization = ""
        file_new.SetCanCreateAltrep(False)

        # --- PDM create operation (drives TC item creation) ---
        op_builder = the_session.PdmSession.CreateCreateOperationBuilder(
            NXOpen.PDM.PartOperationBuilder.OperationType.Create)
        file_new.SetPartOperationCreateBuilder(op_builder)
        op_builder.SetOperationSubType(
            NXOpen.PDM.PartOperationCreateBuilder.OperationSubType.FromTemplate)
        op_builder.SetModelType("master")
        op_builder.SetItemType(item_type)

        logical_objects = op_builder.CreateLogicalObjects()
        source_objects = logical_objects[0].GetUserAttributeSourceObjects()

        # Default the destination folder to the logged-in Teamcenter user.
        if destination_folder is None:
            destination_folder = the_session.PdmSession.GetUserName()
        op_builder.DefaultDestinationFolder = destination_folder

        # COTS parts are not auto-numbered; the part number is entered below as
        # the DB_PART_NO attribute. Registering an empty naming map mirrors the
        # recorded File > New > Item flow for BE9_COTS.
        naming_map = op_builder.CreateAttributeTitleToNamingPatternMap([], [])
        error_list = op_builder.AutoAssignAttributesWithNamingPattern(
            [logical_objects[0]], [naming_map])
        error_list.Dispose()

        # --- Set attributes on the new item ---
        attr_builder = the_session.AttributeManager.CreateAttributePropertiesBuilder(
            NXOpen.BasePart.Null, [],
            NXOpen.AttributePropertiesBuilder.OperationType.Create)
        attr_builder.SetAttributeObjects([source_objects[0]])

        # Item-level attributes (category = item_type, e.g. BE9_COTS).
        attr_builder.Category = item_type
        attr_builder.Title = "DB_PART_NO"
        attr_builder.StringValue = part_no
        attr_builder.CreateAttribute()

        attr_builder.Title = "DB_PART_NAME"
        attr_builder.StringValue = part_name
        attr_builder.CreateAttribute()

        attr_builder.Title = "DB_PART_DESC"
        attr_builder.StringValue = description
        attr_builder.CreateAttribute()

        # Revision-level attributes (category = revision_category).
        attr_builder.Category = revision_category
        attr_builder.Title = "HE_Manufacturer"
        attr_builder.StringValue = manufacturer
        attr_builder.CreateAttribute()

        attr_builder.Title = "Part Class"
        attr_builder.StringValue = part_class
        attr_builder.CreateAttribute()

        # --- Finalize and commit ---
        file_new.MasterFileName = ""
        file_new.MakeDisplayedPart = make_displayed
        file_new.DisplayPartOption = NXOpen.DisplayPartOption.AllowAdditional

        op_builder.ValidateLogicalObjectsToCommit()
        op_builder.CreateSpecificationsForLogicalObjects([logical_objects[0]])

        file_new.Commit()
    finally:
        file_new.Destroy()
        if attr_builder is not None:
            attr_builder.Destroy()

    return the_session.Parts.Work


def list_templates():
    """Return (name, units, is_blank) tuples for all registered templates.

    Useful for discovering the valid template refs on your Teamcenter setup
    (e.g. to confirm "@DB/model-plain-1-inch-template/A"), and for finding
    presentation names / item types alongside the File > New dialog.
    """
    the_session = NXOpen.Session.GetSession()
    file_new = the_session.Parts.FileNew()
    try:
        result = []
        for template in file_new.GetTemplates():
            try:
                result.append(
                    (template.GetName(), template.GetUnits(), template.IsBlank()))
            finally:
                template.Dispose()
        return result
    finally:
        file_new.Destroy()


# The BlockStyler dialog layout lives next to this module.
_DIALOG_DLX = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "create_VENDOR_part_dialog.dlx")


def prompt_cots_attributes(dlx_path=_DIALOG_DLX):
    """Show the Create Vendor Part BlockStyler dialog and read its fields.

    Returns a dict with keys part_no, part_name, part_desc, manufacturer,
    part_class (all stripped strings), or None if the user cancels.

    BlockStyler dialogs require callback handlers to be registered (NX errors
    with "The Initialize callback is not registered" otherwise). We register
    the mandatory ones and capture the field values in the OK/Apply callback,
    which is the reliable place to read block values.
    """
    the_ui = NXOpen.UI.GetUI()
    dialog = the_ui.CreateDialog(dlx_path)
    captured = {}

    def initialize_cb():
        pass

    def update_cb(block):
        return 0

    def apply_cb():
        captured["part_no"] = dialog.GetBlockProperties("partNo").GetString("Value")
        captured["part_name"] = dialog.GetBlockProperties("partName").GetString("Value")
        captured["part_desc"] = dialog.GetBlockProperties("partDesc").GetString("Value")
        captured["manufacturer"] = dialog.GetBlockProperties("manufacturer").GetString("Value")
        captured["part_class"] = dialog.GetBlockProperties("partClass").GetString("Value")
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
        return {key: (captured.get(key) or "").strip() for key in (
            "part_no", "part_name", "part_desc", "manufacturer", "part_class")}
    finally:
        dialog.Dispose()


def main():
    """Entry point when the module is executed directly inside NX.

    Prompts for the vendor part fields via a BlockStyler dialog, then creates
    the part in Teamcenter managed mode as a BE9_COTS item using the
    "@DB/model-plain-1-inch-template/A" template.
    """
    the_session = NXOpen.Session.GetSession()
    lw = the_session.ListingWindow
    lw.Open()

    vendor = prompt_cots_attributes()
    if vendor is None:
        lw.WriteLine("Cancelled: dialog dismissed.")
        return
    if not vendor["part_no"]:
        lw.WriteLine("Cancelled: no part number entered.")
        return

    # Fetch McMaster property data for the entered part number and log it.
    # (For now this is informational only — it does not change the attributes
    # written below.)
    try:
        scraped = scrape_mcmaster_part(vendor["part_no"])
        log_scraped_data(lw, scraped)
    except Exception as ex:  # never let a scrape problem block part creation
        lw.WriteLine("McMaster scrape skipped: {0}".format(ex))

    try:
        part = create_part_cots(
            part_no=vendor["part_no"],
            part_name=vendor["part_name"],
            description=vendor["part_desc"],
            manufacturer=vendor["manufacturer"],
            part_class=vendor["part_class"] or "Class III",
        )
        lw.WriteLine("Created COTS part: {0}".format(part.Leaf))
    except NXOpen.NXException as ex:
        lw.WriteLine("Failed to create COTS part: {0}".format(ex))
        raise


if __name__ == "__main__":
    main()
