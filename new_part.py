# NX 2506
# Journal created by br435t on Fri Jul 10 16:19:53 2026 Pacific Daylight Time
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
    
    partOperationCreateBuilder1.DefaultDestinationFolder = "br435t"
    
    sourceobjects2 = logicalobjects1[0].GetUserAttributeSourceObjects()
    
    partOperationCreateBuilder1.SetOperationSubType(NXOpen.PDM.PartOperationCreateBuilder.OperationSubType.FromTemplate)
    
    sourceobjects3 = logicalobjects1[0].GetUserAttributeSourceObjects()
    
    theSession.SetUndoMarkName(markId1, "New Dialog")
    
    attributetitles1 = [None] * 1 
    attributetitles1[0] = "DB_PART_NO"
    titlepatterns1 = [None] * 1 
    titlepatterns1[0] = "NNNNNNN\"-\"NNN"
    nXObject1 = partOperationCreateBuilder1.CreateAttributeTitleToNamingPatternMap(attributetitles1, titlepatterns1)
    
    objects1 = [NXOpen.NXObject.Null] * 1 
    objects1[0] = logicalobjects1[0]
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
    objects4[0] = sourceobjects1[0]
    attributePropertiesBuilder1.SetAttributeObjects(objects4)
    
    attributePropertiesBuilder1.Title = "DB_PART_NAME"
    
    attributePropertiesBuilder1.Category = "BE9_Design"
    
    attributePropertiesBuilder1.StringValue = "test name"
    
    attributePropertiesBuilder1.Category = "BE9_Design"
    
    changed1 = attributePropertiesBuilder1.CreateAttribute()
    
    attributePropertiesBuilder1.Title = "DB_PART_DESC"
    
    attributePropertiesBuilder1.StringValue = "test description"
    
    attributePropertiesBuilder1.Category = "BE9_Design"
    
    changed2 = attributePropertiesBuilder1.CreateAttribute()
    
    attributePropertiesBuilder1.Title = "Part Class"
    
    attributePropertiesBuilder1.Category = "BE9_DesignRevision"
    
    attributePropertiesBuilder1.StringValue = "Class III"
    
    attributePropertiesBuilder1.Category = "BE9_DesignRevision"
    
    changed3 = attributePropertiesBuilder1.CreateAttribute()
    
    markId2 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "New")
    
    theSession.DeleteUndoMark(markId2, None)
    
    markId3 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "New")
    
    fileNew1.MasterFileName = ""
    
    fileNew1.MakeDisplayedPart = True
    
    fileNew1.DisplayPartOption = NXOpen.DisplayPartOption.AllowAdditional
    
    partOperationCreateBuilder1.ValidateLogicalObjectsToCommit()
    
    logicalobjects2 = [NXOpen.PDM.LogicalObject.Null] * 1 
    logicalobjects2[0] = logicalobjects1[0]
    partOperationCreateBuilder1.CreateSpecificationsForLogicalObjects(logicalobjects2)
    
    errorMessageHandler2 = partOperationCreateBuilder1.GetErrorMessageHandler(True)
    
    errorMessageHandler3 = partOperationCreateBuilder1.GetErrorMessageHandler(True)
    
    nXObject2 = fileNew1.Commit()
    
    workPart = theSession.Parts.Work # 1135393-001.01/test name
    displayPart = theSession.Parts.Display # 1135393-001.01/test name
    errorMessageHandler4 = partOperationCreateBuilder1.GetErrorMessageHandler(True)
    
    theSession.DeleteUndoMark(markId3, None)
    
    fileNew1.Destroy()
    
    attributePropertiesBuilder1.Destroy()
    
    # ----------------------------------------------
    #   Menu: Tools->Automation->Journal->Stop Recording
    # ----------------------------------------------
    
if __name__ == '__main__':
    main(sys.argv[1:])