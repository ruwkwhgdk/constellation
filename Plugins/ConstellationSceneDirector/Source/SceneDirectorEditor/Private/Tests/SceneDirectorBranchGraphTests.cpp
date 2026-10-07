#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "SceneDirectorGraph.h"
#include "EdGraph/EdGraphPin.h"
#include "Editor.h"
#include "ScopedTransaction.h"
#include "UObject/Package.h"
#include "UObject/SavePackage.h"
#include "PackageTools.h"
#include "Misc/Paths.h"

static USceneDirectorAsset* BranchGraphAsset()
{
    auto* A=NewObject<USceneDirectorAsset>(GetTransientPackage(),NAME_None,RF_Transactional);
    A->Steps.SetNum(4);A->Steps[0].Type=EDirectorNodeType::Start;A->Steps[1].Type=EDirectorNodeType::Dialogue;
    A->Steps[2].Type=EDirectorNodeType::Wait;A->Steps[3].Type=EDirectorNodeType::End;
    for(const TCHAR* Key:{TEXT("A"),TEXT("B")}){FDirectorChoice C;C.Key=Key;C.Text=FText::FromString(Key);A->Steps[1].Choices.Add(C);}
    A->Steps[0].NextNodes={A->Steps[1].Id};A->Steps[1].ChoiceTargets.Add(TEXT("A"),A->Steps[2].Id);A->Steps[1].ChoiceTargets.Add(TEXT("B"),A->Steps[3].Id);
    return A;
}
static USceneDirectorGraph* BranchGraph(USceneDirectorAsset* A)
{auto* G=NewObject<USceneDirectorGraph>(GetTransientPackage(),NAME_None,RF_Transactional);G->Asset=A;G->Schema=USceneDirectorSchema::StaticClass();G->Load();return G;}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorBranchPinsTest,"Constellation.SceneDirector.BranchPinsRoundtripUndo",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorBranchPinsTest::RunTest(const FString&)
{
    auto* A=BranchGraphAsset();auto* G=BranchGraph(A);auto* N=CastChecked<USceneDirectorGraphNode>(G->Nodes[1]);
    const FGuid Left=A->Steps[2].Id,Right=A->Steps[3].Id;
    TestNull(TEXT("Choice dialogue has no ordinary parallel output"),N->FindPin(TEXT("Out")));
    FDirectorStep Before=N->Step;N->Step.Choices.Swap(0,1);N->RebuildBranchPins(Before);G->Sync();
    TestEqual(TEXT("Reorder keeps A target"),A->Steps[1].ChoiceTargets.FindRef(TEXT("A")),Left);
    TestEqual(TEXT("Reorder keeps B target"),A->Steps[1].ChoiceTargets.FindRef(TEXT("B")),Right);
    Before=N->Step;N->Step.Choices[0].Key=TEXT("Renamed");N->RebuildBranchPins(Before);G->Sync();
    TestEqual(TEXT("Rename at same position keeps target"),A->Steps[1].ChoiceTargets.FindRef(TEXT("Renamed")),Right);
    TestFalse(TEXT("Old key removed"),A->Steps[1].ChoiceTargets.Contains(TEXT("B")));
    {
        FScopedTransaction Tx(FText::FromString(TEXT("Delete test choice")));N->Modify();Before=N->Step;
        N->Step.Choices.RemoveAt(0);N->RebuildBranchPins(Before);G->Sync();
    }
    TestFalse(TEXT("Deleted target removed"),A->Steps[1].ChoiceTargets.Contains(TEXT("Renamed")));
    TestTrue(TEXT("Deleted output removes reciprocal input link"),G->Nodes[3]->FindPin(TEXT("In"))->LinkedTo.IsEmpty());
    GEditor->UndoTransaction();G->Load();
    TestEqual(TEXT("Undo restores choices"),A->Steps[1].Choices.Num(),2);
    TestEqual(TEXT("Undo restores removed target"),A->Steps[1].ChoiceTargets.FindRef(TEXT("Renamed")),Right);
    GEditor->RedoTransaction();
    TestEqual(TEXT("Redo restores asset before graph reload"),A->Steps[1].Choices.Num(),1);
    G->Load();TestEqual(TEXT("Redo deletes choice"),A->Steps[1].Choices.Num(),1);
    N=CastChecked<USceneDirectorGraphNode>(G->Nodes[1]);auto* Pin=N->FindPin(USceneDirectorGraphNode::ChoicePinName(TEXT("A")));
    TestEqual(TEXT("Exclusive output replaces old target"),G->GetSchema()->CanCreateConnection(Pin,G->Nodes[3]->FindPin(TEXT("In"))).Response,CONNECT_RESPONSE_BREAK_OTHERS_A);
    TestEqual(TEXT("Cycle checks choice outputs"),G->GetSchema()->CanCreateConnection(G->Nodes[2]->FindPin(TEXT("Out")),N->FindPin(TEXT("In"))).Response,CONNECT_RESPONSE_DISALLOW);
    // Both answers may share a join target, but a single answer still has only one outgoing edge.
    G->GetSchema()->TryCreateConnection(Pin,G->Nodes[3]->FindPin(TEXT("In")));G->Sync();G->Load();
    TestEqual(TEXT("Reopen follows replacement"),A->Steps[1].ChoiceTargets.FindRef(TEXT("A")),Right);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorBranchLegacyPinsTest,"Constellation.SceneDirector.BranchLegacyAndConditionPins",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorBranchLegacyPinsTest::RunTest(const FString&)
{
    auto* A=BranchGraphAsset();A->Steps[1].ChoiceTargets.Reset();A->Steps[1].NextNodes={A->Steps[2].Id};
    auto* G=BranchGraph(A);G->Sync();
    for(FName Key:{FName(TEXT("A")),FName(TEXT("B"))})TestEqual(TEXT("One legacy continuation migrates every answer"),A->Steps[1].ChoiceTargets.FindRef(Key),A->Steps[2].Id);
    TestTrue(TEXT("Legacy ordinary target consumed"),A->Steps[1].NextNodes.IsEmpty());
    A->Steps[1].ChoiceTargets.Reset();A->Steps[1].NextNodes={A->Steps[2].Id,A->Steps[3].Id};G->Load();G->Sync();
    TestEqual(TEXT("Ambiguous legacy targets retained"),A->Steps[1].NextNodes.Num(),2);
    TestFalse(TEXT("Ambiguous legacy target never chosen silently"),A->Steps[1].ChoiceTargets.FindRef(TEXT("A")).IsValid());
    A->Steps[1].Type=EDirectorNodeType::Condition;A->Steps[1].TrueTarget=A->Steps[2].Id;A->Steps[1].FalseTarget=A->Steps[3].Id;
    G->Load();G->Sync();TestEqual(TEXT("True roundtrip"),A->Steps[1].TrueTarget,A->Steps[2].Id);TestEqual(TEXT("False roundtrip"),A->Steps[1].FalseTarget,A->Steps[3].Id);
    FDirectorBoolEntry B;B.Key=TEXT("Before");A->BoolVariables.Add(B);A->Steps[1].BoolKey=B.Key;
    A->PreEditChange(nullptr);A->BoolVariables[0].Key=TEXT("After");FPropertyChangedEvent Event(nullptr);A->PostEditChangeProperty(Event);
    TestEqual(TEXT("Bool registry rename propagates"),A->Steps[1].BoolKey,FName(TEXT("After")));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorBranchPinSaveTest,"Constellation.SceneDirector.BranchPinSaveReopen",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorBranchPinSaveTest::RunTest(const FString&)
{
    const FString Name=TEXT("/Temp/BranchPins_")+FGuid::NewGuid().ToString(EGuidFormats::Digits);
    UPackage* Package=CreatePackage(*Name);auto* A=DuplicateObject<USceneDirectorAsset>(BranchGraphAsset(),Package,TEXT("BranchPins"));A->SetFlags(RF_Public|RF_Standalone);
    const FGuid Left=A->Steps[2].Id,Right=A->Steps[3].Id;A->Steps[1].Choices.Swap(0,1);
    const FString File=FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir()/TEXT("SceneDirector-branch-pins.uasset"));
    FSavePackageArgs Args;Args.TopLevelFlags=RF_Public|RF_Standalone;Args.SaveFlags=SAVE_NoError;
    if(!TestTrue(TEXT("Save branch pins"),UPackage::SavePackage(Package,A,*File,Args)))return false;
    Package->SetDirtyFlag(false);A=nullptr;TArray<UPackage*> Packages{Package};if(!TestTrue(TEXT("Unload"),UPackageTools::UnloadPackages(Packages)))return false;
    auto* Reloaded=LoadPackage(nullptr,*File,LOAD_None);if(!TestNotNull(TEXT("Reload"),Reloaded))return false;
    A=FindObject<USceneDirectorAsset>(Reloaded,TEXT("BranchPins"));if(!TestNotNull(TEXT("Restored asset"),A))return false;
    auto* G=BranchGraph(A);G->Sync();TestEqual(TEXT("Saved order"),A->Steps[1].Choices[0].Key,FName(TEXT("B")));
    TestEqual(TEXT("Saved A target"),A->Steps[1].ChoiceTargets.FindRef(TEXT("A")),Left);TestEqual(TEXT("Saved B target"),A->Steps[1].ChoiceTargets.FindRef(TEXT("B")),Right);return true;
}
#endif
