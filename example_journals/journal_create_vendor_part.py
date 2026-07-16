# NX 2506
# Journal created by br435t on Thu Jul 16 12:03:45 2026 Pacific Daylight Time
#
import math
import NXOpen
import NXOpen.PDM
def main(args) : 

    theSession  = NXOpen.Session.GetSession() #type: NXOpen.Session
    workPart = theSession.Parts.Work
    displayPart = theSession.Parts.Display
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
    
    partOperationCreateBuilder1.DefaultDestinationFolder = ":MCMASTER"
    
    sourceobjects2 = logicalobjects1[0].GetUserAttributeSourceObjects()
    
    partOperationCreateBuilder1.SetOperationSubType(NXOpen.PDM.PartOperationCreateBuilder.OperationSubType.FromTemplate)
    
    sourceobjects3 = logicalobjects1[0].GetUserAttributeSourceObjects()
    
    theSession.SetUndoMarkName(markId1, "New Dialog")
    
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
    
    partOperationCreateBuilder1.SetAddMaster(False)
    
    partOperationCreateBuilder1.SetItemType("BE9_COTS")
    
    logicalobjects2 = partOperationCreateBuilder1.CreateLogicalObjects()
    
    sourceobjects4 = logicalobjects2[0].GetUserAttributeSourceObjects()
    
    logicalobjects3 = partOperationCreateBuilder1.CreateLogicalObjects()
    
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
    
    attributePropertiesBuilder1.StringValue = "91310A532"
    
    attributePropertiesBuilder1.Category = "BE9_COTS"
    
    changed1 = attributePropertiesBuilder1.CreateAttribute()
    
    attributePropertiesBuilder1.Title = "DB_PART_NAME"
    
    attributePropertiesBuilder1.StringValue = "High-Strength Class 10.9 Steel Hex Head Screw\nZinc-Plated, M8 x 1.25 mm Thread Size, 30 mm Long"
    
    attributePropertiesBuilder1.Category = "BE9_COTS"
    
    changed2 = attributePropertiesBuilder1.CreateAttribute()
    
    attributePropertiesBuilder1.Title = "DB_PART_DESC"
    
    attributePropertiesBuilder1.Category = "BE9_COTS"
    
    changed3 = attributePropertiesBuilder1.CreateAttribute()
    
    attributePropertiesBuilder1.Title = "HE_Manufacturer"
    
    attributePropertiesBuilder1.Category = "BE9_COTSRevision"
    
    attributePropertiesBuilder1.StringValue = "MCMASTER"
    
    attributePropertiesBuilder1.Category = "BE9_COTSRevision"
    
    changed4 = attributePropertiesBuilder1.CreateAttribute()
    
    attributePropertiesBuilder1.Title = "Part Class"
    
    attributePropertiesBuilder1.StringValue = "Class III"
    
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
    
    logicalobjects4 = [NXOpen.PDM.LogicalObject.Null] * 1 
    logicalobjects4[0] = logicalobjects2[0]
    partOperationCreateBuilder1.CreateSpecificationsForLogicalObjects(logicalobjects4)
    
    errorMessageHandler2 = partOperationCreateBuilder1.GetErrorMessageHandler(True)
    
    errorMessageHandler3 = partOperationCreateBuilder1.GetErrorMessageHandler(True)
    
    nXObject2 = fileNew1.Commit()
    
    workPart = theSession.Parts.Work # 91310A532.A/High-Strength Class 10.9 Steel Hex Head Screw
    Zinc-Plated, M8 x 1.25 mm Thread Size, 30 mm Long
    displayPart = theSession.Parts.Display # 91310A532.A/High-Strength Class 10.9 Steel Hex Head Screw
    Zinc-Plated, M8 x 1.25 mm Thread Size, 30 mm Long
    errorMessageHandler4 = partOperationCreateBuilder1.GetErrorMessageHandler(True)
    
    theSession.DeleteUndoMark(markId3, None)
    
    fileNew1.Destroy()
    
    attributePropertiesBuilder1.Destroy()
    
    # ----------------------------------------------
    #   Menu: Tools->Automation->Journal->Stop Recording
    # ----------------------------------------------
    
if __name__ == '__main__':
    main(sys.argv[1:])