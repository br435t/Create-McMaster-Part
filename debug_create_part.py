"""debug_create_part.py  -  standalone Teamcenter COTS create, for debugging.

Creates a BE9_COTS part with HARDCODED attribute values (no scraper, no
BlockStyler dialogs) so the managed-mode create can be tested in isolation.
Everything is logged to the Listing Window, and the PDM error/warning messages
are dumped after each stage so a failing Commit() explains itself.

Run in NX:  File > Execute > NX Open...  ->  debug_create_part.py

This mirrors the KNOWN-GOOD recording journal_create_vendorpart.py. Flip the
flags below to bisect what actually matters for a successful commit.
"""
import NXOpen
import NXOpen.PDM

# ---- test values (edit freely) ------------------------------------------
PART_NO = "DEBUG0001"
PART_NAME = "DEBUG NAME"
PART_DESC = "DEBUG DESCRIPTION 1/4\" x 20"   # note: intentionally has / and "
MANUFACTURER = "MCMASTER"
PART_CLASS = "Class III"

DEST_FOLDER = "br435t"
TEMPLATE = "@DB/model-plain-1-inch-template/A"
ITEM_TYPE = "BE9_COTS"
ITEM_TYPES = "BE9_Design,BE9_Electrical,BE9_COTS,BE9_Tooling"
ITEM_CATEGORY = "BE9_COTS"
REV_CATEGORY = "BE9_COTSRevision"

# ---- bisect flags (all True == faithful to the working recording) -------
USE_DESIGN_DETOUR = True      # do the BE9_Design CreateLogicalObjects first
CALL_SET_ADD_MASTER = True    # opBuilder.SetAddMaster(False)
DOUBLE_CREATE_LOGICAL = True  # call CreateLogicalObjects twice for COTS
SET_DB_PART_NO_ATTR = True    # set DB_PART_NO as a plain attribute
CALL_VALIDATE = True          # call ValidateLogicalObjectsToCommit before commit
CALL_CREATE_SPECS = True      # call CreateSpecificationsForLogicalObjects
# When True, assign DB_PART_NO via a quoted-literal NAMING PATTERN (the same
# mechanism the working Design flow uses, which generates a valid filename)
# instead of an empty map + plain attribute. This is the promising fix for the
# "new filename is not a valid file specification" error.
USE_NAMING_PATTERN = True


def _log(lw, msg):
    lw.WriteLine(msg)


def _dump_errors(lw, opBuilder, label):
    """Print PDM error/warning messages for the current builder state.

    Fully defensive: the NXOpen binding for GetErrorMessages() can raise
    SystemError ("error return without exception set") in some states, so each
    getter is guarded and never aborts the run.
    """
    try:
        handler = opBuilder.GetErrorMessageHandler(True)
    except Exception as ex:
        _log(lw, "  [{0}] GetErrorMessageHandler failed: {1}".format(label, ex))
        return
    errs, warns = [], []
    try:
        errs = list(handler.GetErrorMessages() or [])
    except Exception as ex:
        _log(lw, "  [{0}] GetErrorMessages failed: {1}".format(label, ex))
    try:
        warns = list(handler.GetWarningMessages() or [])
    except Exception as ex:
        _log(lw, "  [{0}] GetWarningMessages failed: {1}".format(label, ex))
    if not errs and not warns:
        _log(lw, "  [{0}] (no messages)".format(label))
    for e in errs:
        _log(lw, "  [{0}] ERROR: {1}".format(label, e))
    for w in warns:
        _log(lw, "  [{0}] warn : {1}".format(label, w))
    try:
        handler.Dispose()
    except Exception:
        pass


def main(args):
    theSession = NXOpen.Session.GetSession()
    lw = theSession.ListingWindow
    lw.Open()
    _log(lw, "=" * 60)
    _log(lw, "debug_create_part.py")
    _log(lw, "  PART_NO={0!r}  ITEM_TYPE={1}".format(PART_NO, ITEM_TYPE))
    _log(lw, "  flags: detour={0} addMaster={1} doubleCLO={2} dbPartNoAttr={3} namingPattern={4}".format(
        USE_DESIGN_DETOUR, CALL_SET_ADD_MASTER, DOUBLE_CREATE_LOGICAL,
        SET_DB_PART_NO_ATTR, USE_NAMING_PATTERN))
    _log(lw, "=" * 60)

    fileNew = theSession.Parts.FileNew()
    attrBuilder = None
    try:
        fileNew.TemplateFileName = TEMPLATE
        fileNew.UseBlankTemplate = False
        fileNew.ApplicationName = "ModelTemplate"
        fileNew.Units = NXOpen.Part.Units.Inches
        fileNew.RelationType = "master"
        fileNew.UsesMasterModel = "No"
        fileNew.TemplateType = NXOpen.FileNewTemplateType.Item
        fileNew.TemplatePresentationName = "Model"
        fileNew.ItemType = ITEM_TYPES
        fileNew.Specialization = ""
        fileNew.SetCanCreateAltrep(False)
        _log(lw, "[ok] template configured")

        opBuilder = theSession.PdmSession.CreateCreateOperationBuilder(
            NXOpen.PDM.PartOperationBuilder.OperationType.Create)
        fileNew.SetPartOperationCreateBuilder(opBuilder)
        opBuilder.SetOperationSubType(
            NXOpen.PDM.PartOperationCreateBuilder.OperationSubType.FromTemplate)
        opBuilder.SetModelType("master")

        if USE_DESIGN_DETOUR:
            opBuilder.SetItemType("BE9_Design")
            lo1 = opBuilder.CreateLogicalObjects()
            lo1[0].GetUserAttributeSourceObjects()
            opBuilder.DefaultDestinationFolder = DEST_FOLDER
            opBuilder.SetOperationSubType(
                NXOpen.PDM.PartOperationCreateBuilder.OperationSubType.FromTemplate)
            _log(lw, "[ok] BE9_Design detour")
        else:
            opBuilder.DefaultDestinationFolder = DEST_FOLDER

        if CALL_SET_ADD_MASTER:
            opBuilder.SetAddMaster(False)
            _log(lw, "[ok] SetAddMaster(False)")

        opBuilder.SetItemType(ITEM_TYPE)
        logicalObjects = opBuilder.CreateLogicalObjects()
        sourceObjects = logicalObjects[0].GetUserAttributeSourceObjects()
        if DOUBLE_CREATE_LOGICAL:
            opBuilder.CreateLogicalObjects()
        _log(lw, "[ok] {0} logical objects".format(ITEM_TYPE))

        if USE_NAMING_PATTERN:
            # Quoted literal -> assign PART_NO as the number AND generate the
            # filename (same path as the working Design flow).
            titles = ["DB_PART_NO"]
            patterns = ['"' + PART_NO + '"']
            _log(lw, "[..] naming pattern: DB_PART_NO = {0}".format(patterns[0]))
        else:
            titles, patterns = [], []
            _log(lw, "[..] empty naming map (DB_PART_NO via attribute)")
        namingMap = opBuilder.CreateAttributeTitleToNamingPatternMap(titles, patterns)
        errorList = opBuilder.AutoAssignAttributesWithNamingPattern(
            [logicalObjects[0]], [namingMap])
        errorList.Dispose()
        _dump_errors(lw, opBuilder, "after AutoAssign")

        attrBuilder = theSession.AttributeManager.CreateAttributePropertiesBuilder(
            NXOpen.BasePart.Null, [],
            NXOpen.AttributePropertiesBuilder.OperationType.Create)
        attrBuilder.SetAttributeObjects([sourceObjects[0]])

        attrBuilder.Category = ITEM_CATEGORY
        # Only set DB_PART_NO as a plain attribute when NOT using the naming
        # pattern (the pattern already assigns it).
        if SET_DB_PART_NO_ATTR and not USE_NAMING_PATTERN:
            attrBuilder.Title = "DB_PART_NO"
            attrBuilder.StringValue = PART_NO
            attrBuilder.CreateAttribute()
        attrBuilder.Title = "DB_PART_NAME"
        attrBuilder.StringValue = PART_NAME
        attrBuilder.CreateAttribute()
        attrBuilder.Title = "DB_PART_DESC"
        attrBuilder.StringValue = PART_DESC
        attrBuilder.CreateAttribute()
        attrBuilder.Category = REV_CATEGORY
        attrBuilder.Title = "HE_Manufacturer"
        attrBuilder.StringValue = MANUFACTURER
        attrBuilder.CreateAttribute()
        attrBuilder.Title = "Part Class"
        attrBuilder.StringValue = PART_CLASS
        attrBuilder.CreateAttribute()
        _log(lw, "[ok] attributes set")

        fileNew.MasterFileName = ""
        fileNew.MakeDisplayedPart = True
        fileNew.DisplayPartOption = NXOpen.DisplayPartOption.AllowAdditional

        if CALL_VALIDATE:
            _log(lw, "[..] ValidateLogicalObjectsToCommit ...")
            try:
                opBuilder.ValidateLogicalObjectsToCommit()
            except Exception as ex:
                _log(lw, "[FAIL] Validate raised: {0}".format(ex))
                _dump_errors(lw, opBuilder, "Validate fail")
                raise
            _dump_errors(lw, opBuilder, "after Validate")
        else:
            _log(lw, "[skip] ValidateLogicalObjectsToCommit")

        if CALL_CREATE_SPECS:
            _log(lw, "[..] CreateSpecificationsForLogicalObjects ...")
            try:
                opBuilder.CreateSpecificationsForLogicalObjects([logicalObjects[0]])
            except Exception as ex:
                _log(lw, "[FAIL] CreateSpecs raised: {0}".format(ex))
                _dump_errors(lw, opBuilder, "CreateSpecs fail")
                raise
            _dump_errors(lw, opBuilder, "after CreateSpecs")
        else:
            _log(lw, "[skip] CreateSpecificationsForLogicalObjects")

        _log(lw, "[..] fileNew.Commit() ...")
        try:
            fileNew.Commit()
        except Exception as ex:
            _log(lw, "[FAIL] Commit raised: {0}".format(ex))
            _dump_errors(lw, opBuilder, "Commit fail")
            raise

        workPart = theSession.Parts.Work
        _log(lw, "[SUCCESS] created: {0}".format(workPart.Leaf))
    finally:
        try:
            fileNew.Destroy()
        except Exception:
            pass
        if attrBuilder is not None:
            try:
                attrBuilder.Destroy()
            except Exception:
                pass
        theSession.CleanUpFacetedFacesAndEdges()


if __name__ == '__main__':
    main(None)
