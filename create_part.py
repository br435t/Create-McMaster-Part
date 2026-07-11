"""create_part.py

Reusable helper for creating a new NX part with NX Open (Python).

Tested against the Siemens NX 2506 NXOpen Python API.

Run inside NX (File > Execute > NX Open...) or via `run_journal`, e.g.:

    py -m create_part                 # not valid: NXOpen only exists inside NX
    (NX) Execute -> select create_part.py

or import and call from another journal:

    from create_part import create_part
    part = create_part(r"C:\\temp\\MyPart.prt")
"""

import os

import NXOpen
import NXOpen.PDM
import NXOpen.BlockStyler


def create_part(
    new_file_name,
    template_file_name="model-plain-1-mm-template.prt",
    application_name="ModelTemplate",
    presentation_name="Model",
    units=NXOpen.Part.Units.Millimeters,
    use_blank_template=False,
    make_displayed=True,
):
    """Create a new NX part and return it.

    Args:
        new_file_name:       Full path of the .prt file to create.
        template_file_name:  Seed template part. Ignored if use_blank_template.
        application_name:    Application type, e.g. "ModelTemplate".
                             Call FileNew.GetApplicationNames() for valid values.
        presentation_name:   Template presentation name, e.g. "Model".
        units:               NXOpen.Part.Units.Millimeters or .Inches.
        use_blank_template:  True to create without a template (blank part).
        make_displayed:      Make the new part the displayed part.

    Returns:
        The newly created NXOpen.Part (the session's work part).
    """
    the_session = NXOpen.Session.GetSession()
    file_new = the_session.Parts.FileNew()

    try:
        file_new.TemplateType = NXOpen.FileNewTemplateType.Item
        file_new.UseBlankTemplate = use_blank_template

        if not use_blank_template:
            file_new.TemplateFileName = template_file_name
            file_new.ApplicationName = application_name
            file_new.TemplatePresentationName = presentation_name
            file_new.Units = units

        file_new.NewFileName = new_file_name
        file_new.MakeDisplayedPart = make_displayed

        file_new.Commit()
    finally:
        file_new.Destroy()

    return the_session.Parts.Work


def create_part_teamcenter(
    part_name,
    description="",
    part_class="Class III",
    item_type="BE9_Design",
    destination_folder=None,
    template_file_name="@DB/model-plain-1-inch-template/A",
    template_presentation_name="Model",
    application_name="ModelTemplate",
    item_types="BE9_Design,BE9_Electrical,BE9_COTS,BE9_Tooling",
    units=NXOpen.Part.Units.Inches,
    naming_attribute="DB_PART_NO",
    naming_pattern='NNNNNNN"-"NNN',
    make_displayed=True,
):
    """Create a new part in Teamcenter (managed mode) from a template.

    This mirrors the recorded File > New > Item workflow for the BE9 setup.
    The part number is auto-assigned from the naming pattern; the item name,
    description, and part class are written as attributes.

    Args:
        part_name:                  Value for the DB_PART_NAME attribute.
        description:                Value for the DB_PART_DESC attribute.
        part_class:                 Value for the "Part Class" attribute
                                    (category BE9_DesignRevision), e.g. "Class III".
        item_type:                  Item type actually created, e.g. "BE9_Design".
        destination_folder:         Teamcenter destination folder. Defaults to
                                    the logged-in Teamcenter user's home
                                    (PdmSession.GetUserName()) when None.
        template_file_name:         TC template ref, "@DB/<template>/<rev>".
        template_presentation_name: Template name as shown in File > New.
        application_name:           Application type, e.g. "ModelTemplate".
        item_types:                 Comma-separated item types the template
                                    supports (populates the type dropdown).
        units:                      NXOpen.Part.Units.Inches or .Millimeters.
        naming_attribute:           Attribute driving auto-numbering, e.g. DB_PART_NO.
        naming_pattern:             NX naming pattern for the number.
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

        # --- Auto-assign the part number from the naming pattern ---
        naming_map = op_builder.CreateAttributeTitleToNamingPatternMap(
            [naming_attribute], [naming_pattern])
        error_list = op_builder.AutoAssignAttributesWithNamingPattern(
            [logical_objects[0]], [naming_map])
        error_list.Dispose()

        # --- Set descriptive attributes on the new item ---
        attr_builder = the_session.AttributeManager.CreateAttributePropertiesBuilder(
            NXOpen.BasePart.Null, [],
            NXOpen.AttributePropertiesBuilder.OperationType.Create)
        attr_builder.SetAttributeObjects([source_objects[0]])

        attr_builder.Category = "BE9_Design"
        attr_builder.Title = "DB_PART_NAME"
        attr_builder.StringValue = part_name
        attr_builder.CreateAttribute()

        attr_builder.Title = "DB_PART_DESC"
        attr_builder.StringValue = description
        attr_builder.CreateAttribute()

        attr_builder.Category = "BE9_DesignRevision"
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
    os.path.dirname(os.path.abspath(__file__)), "create_part_dialog.dlx")


def prompt_name_and_description(dlx_path=_DIALOG_DLX):
    """Show the Create Part BlockStyler dialog and read its two fields.

    Returns (name, description). Both are None if the user cancels; `name` is
    None if it was left blank.

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
        captured["name"] = dialog.GetBlockProperties("namePart").GetString("Value")
        captured["desc"] = dialog.GetBlockProperties("descPart").GetString("Value")
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
            return None, None
        name = (captured.get("name") or "").strip()
        description = (captured.get("desc") or "").strip()
        return (name or None), description
    finally:
        dialog.Dispose()


def main():
    """Entry point when the module is executed directly inside NX.

    Prompts for the part name and description via a BlockStyler dialog, then
    creates the part in Teamcenter managed mode using the
    "@DB/model-plain-1-inch-template/A" template.
    """
    the_session = NXOpen.Session.GetSession()
    lw = the_session.ListingWindow
    lw.Open()

    part_name, description = prompt_name_and_description()
    if part_name is None:
        lw.WriteLine("Cancelled: no part name entered.")
        return

    try:
        part = create_part_teamcenter(
            part_name=part_name,
            description=description or "",
            part_class="Class III",
        )
        lw.WriteLine("Created part: {0}".format(part.Leaf))
    except NXOpen.NXException as ex:
        lw.WriteLine("Failed to create part: {0}".format(ex))
        raise


if __name__ == "__main__":
    main()
