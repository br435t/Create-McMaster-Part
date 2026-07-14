# NX 2506
# Journal created by br435t on Tue Jul 14 09:12:10 2026 Pacific Daylight Time
#
import os
import sys
import math
import NXOpen
import NXOpen.PDM
import NXOpen.BlockStyler

# BlockStyler dialog layout lives next to this module.
_DIALOG_DLX = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "create_VENDOR_part_dialog.dlx")


def prompt_vendor_attributes(dlx_path=_DIALOG_DLX):
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


def main(args) :

    theSession  = NXOpen.Session.GetSession() #type: NXOpen.Session
    workPart = theSession.Parts.Work
    displayPart = theSession.Parts.Display

    # --- Collect the vendor attribute values from the user (BlockStyler) ---
    vendor = prompt_vendor_attributes()
    if vendor is None:
        return  # user cancelled
    part_no = vendor["part_no"]
    part_name = vendor["part_name"]
    part_desc = vendor["part_desc"]
    manufacturer = vendor["manufacturer"]
    part_class = vendor["part_class"]
    # ----------------------------------------------
    #   Menu: File->New->Item...
    # ----------------------------------------------
    markId1 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "Start")
    
    fileNew1 = theSession.Parts.FileNew()
    
    fileNew1.TemplateFileName = "@DB/model-plain-1-inch-template/A"
    
    fileNew1.UseBlankTemplate = False
    
    fileNew1.ApplicationName = "ModelTemplate"
    
    fileNew1.Units = NXOpen.Part.Units.Inches
    
    fileNew1.RelationType = "master"
    
    fileNew1.UsesMasterModel = "No"
    
    fileNew1.TemplateType = NXOpen.FileNewTemplateType.Item
    
    fileNew1.TemplatePresentationName = "Model"
    
    fileNew1.ItemType = "BE9_Design,BE9_Electrical,BE9_COTS,BE9_Tooling"
    
    fileNew1.Specialization = ""
    
    fileNew1.SetCanCreateAltrep(False)
    
    partOperationCreateBuilder1 = theSession.PdmSession.CreateCreateOperationBuilder(NXOpen.PDM.PartOperationBuilder.OperationType.Create)
    
    fileNew1.SetPartOperationCreateBuilder(partOperationCreateBuilder1)
    
    partOperationCreateBuilder1.SetOperationSubType(NXOpen.PDM.PartOperationCreateBuilder.OperationSubType.FromTemplate)
    
    partOperationCreateBuilder1.SetModelType("master")
    
    partOperationCreateBuilder1.SetItemType("BE9_Design")
    
    logicalobjects1 = partOperationCreateBuilder1.CreateLogicalObjects()
    
    sourceobjects1 = logicalobjects1[0].GetUserAttributeSourceObjects()
    
    partOperationCreateBuilder1.DefaultDestinationFolder = "br435t"
    
    sourceobjects2 = logicalobjects1[0].GetUserAttributeSourceObjects()
    
    partOperationCreateBuilder1.SetOperationSubType(NXOpen.PDM.PartOperationCreateBuilder.OperationSubType.FromTemplate)
    
    sourceobjects3 = logicalobjects1[0].GetUserAttributeSourceObjects()
    
    theSession.SetUndoMarkName(markId1, "New Dialog")
    
    partOperationCreateBuilder1.SetItemType("BE9_COTS")
    
    logicalobjects2 = partOperationCreateBuilder1.CreateLogicalObjects()
    
    sourceobjects4 = logicalobjects2[0].GetUserAttributeSourceObjects()
    
    attributetitles1 = []
    titlepatterns1 = []
    nXObject1 = partOperationCreateBuilder1.CreateAttributeTitleToNamingPatternMap(attributetitles1, titlepatterns1)
    
    objects1 = [NXOpen.NXObject.Null] * 1 
    objects1[0] = logicalobjects2[0]
    properties1 = [NXOpen.NXObject.Null] * 1 
    properties1[0] = nXObject1
    errorList1 = partOperationCreateBuilder1.AutoAssignAttributesWithNamingPattern(objects1, properties1)
    
    errorList1.Dispose()
    errorMessageHandler1 = partOperationCreateBuilder1.GetErrorMessageHandler(True)
    
    objects2 = []
    attributePropertiesBuilder1 = theSession.AttributeManager.CreateAttributePropertiesBuilder(NXOpen.BasePart.Null, objects2, NXOpen.AttributePropertiesBuilder.OperationType.Create)
    
    objects3 = []
    attributePropertiesBuilder1.SetAttributeObjects(objects3)
    
    objects4 = [NXOpen.NXObject.Null] * 1 
    objects4[0] = sourceobjects4[0]
    attributePropertiesBuilder1.SetAttributeObjects(objects4)
    
    attributePropertiesBuilder1.Title = "DB_PART_NO"
    
    attributePropertiesBuilder1.Category = "BE9_COTS"
    
    attributePropertiesBuilder1.StringValue = part_no
    
    attributePropertiesBuilder1.Category = "BE9_COTS"
    
    changed1 = attributePropertiesBuilder1.CreateAttribute()
    
    attributePropertiesBuilder1.Title = "DB_PART_NAME"
    
    attributePropertiesBuilder1.StringValue = part_name
    
    attributePropertiesBuilder1.Category = "BE9_COTS"
    
    changed2 = attributePropertiesBuilder1.CreateAttribute()
    
    attributePropertiesBuilder1.Title = "DB_PART_DESC"
    
    attributePropertiesBuilder1.StringValue = part_desc
    
    attributePropertiesBuilder1.Category = "BE9_COTS"
    
    changed3 = attributePropertiesBuilder1.CreateAttribute()
    
    attributePropertiesBuilder1.Title = "HE_Manufacturer"
    
    attributePropertiesBuilder1.Category = "BE9_COTSRevision"
    
    attributePropertiesBuilder1.StringValue = manufacturer
    
    attributePropertiesBuilder1.Category = "BE9_COTSRevision"
    
    changed4 = attributePropertiesBuilder1.CreateAttribute()
    
    attributePropertiesBuilder1.Title = "Part Class"
    
    attributePropertiesBuilder1.StringValue = part_class
    
    attributePropertiesBuilder1.Category = "BE9_COTSRevision"
    
    changed5 = attributePropertiesBuilder1.CreateAttribute()
    
    markId2 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "New")
    
    theSession.DeleteUndoMark(markId2, None)
    
    markId3 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "New")
    
    fileNew1.TemplateFileName = "@DB/model-plain-1-inch-template/A"
    
    fileNew1.UseBlankTemplate = False
    
    fileNew1.ApplicationName = "ModelTemplate"
    
    fileNew1.Units = NXOpen.Part.Units.Inches
    
    fileNew1.RelationType = "master"
    
    fileNew1.UsesMasterModel = "No"
    
    fileNew1.TemplateType = NXOpen.FileNewTemplateType.Item
    
    fileNew1.TemplatePresentationName = "Model"
    
    fileNew1.ItemType = "BE9_Design,BE9_Electrical,BE9_COTS,BE9_Tooling"
    
    fileNew1.Specialization = ""
    
    fileNew1.SetCanCreateAltrep(False)
    
    fileNew1.MasterFileName = ""
    
    fileNew1.MakeDisplayedPart = True
    
    fileNew1.DisplayPartOption = NXOpen.DisplayPartOption.AllowAdditional
    
    partOperationCreateBuilder1.ValidateLogicalObjectsToCommit()
    
    logicalobjects3 = [NXOpen.PDM.LogicalObject.Null] * 1 
    logicalobjects3[0] = logicalobjects2[0]
    partOperationCreateBuilder1.CreateSpecificationsForLogicalObjects(logicalobjects3)
    
    errorMessageHandler2 = partOperationCreateBuilder1.GetErrorMessageHandler(True)
    
    errorMessageHandler3 = partOperationCreateBuilder1.GetErrorMessageHandler(True)
    
    nXObject2 = fileNew1.Commit()
    
    workPart = theSession.Parts.Work # vendor_PN.A/vendor_Name
    displayPart = theSession.Parts.Display # vendor_PN.A/vendor_Name
    errorMessageHandler4 = partOperationCreateBuilder1.GetErrorMessageHandler(True)
    
    theSession.DeleteUndoMark(markId3, None)
    
    fileNew1.Destroy()
    
    attributePropertiesBuilder1.Destroy()
    
    theSession.CleanUpFacetedFacesAndEdges()
    
    # ----------------------------------------------
    #   Menu: Tools->Automation->Journal->Stop Recording
    # ----------------------------------------------
    
if __name__ == '__main__':
    main(sys.argv[1:])