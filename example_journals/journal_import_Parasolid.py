# NX 2506
# Journal created by br435t on Tue Jul 14 10:35:52 2026 Pacific Daylight Time
#
import math
import NXOpen
def main(args) : 

    theSession  = NXOpen.Session.GetSession() #type: NXOpen.Session
    workPart = theSession.Parts.Work
    displayPart = theSession.Parts.Display
    # ----------------------------------------------
    #   Menu: File->Import->Parasolid...
    # ----------------------------------------------
    markId1 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "Start")
    
    parasolidImporter1 = theSession.DexManager.CreateParasolidImporter()
    
    parasolidImporter1.ObjectTypes.Curves = True
    
    parasolidImporter1.ObjectTypes.Surfaces = True
    
    parasolidImporter1.ObjectTypes.Solids = True
    
    theSession.SetUndoMarkName(markId1, "Import Parasolid Dialog")
    
    parasolidImporter1.SetMode(NXOpen.BaseImporter.Mode.NativeFileSystem)
    
    parasolidImporter1.InputFile = "C:\\TEMP\\MCMASTER\\8880T951_NO THREADS_Steel U-Bolt.X_T"
    
    markId2 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "Import Parasolid")
    
    theSession.DeleteUndoMark(markId2, None)
    
    markId3 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "Import Parasolid")
    
    nXObject1 = parasolidImporter1.Commit()
    
    theSession.DeleteUndoMark(markId3, None)
    
    theSession.SetUndoMarkName(markId1, "Import Parasolid")
    
    parasolidImporter1.Destroy()
    
    theSession.CleanUpFacetedFacesAndEdges()
    
    # ----------------------------------------------
    #   Menu: Tools->Automation->Journal->Stop Recording
    # ----------------------------------------------
    
if __name__ == '__main__':
    main(sys.argv[1:])