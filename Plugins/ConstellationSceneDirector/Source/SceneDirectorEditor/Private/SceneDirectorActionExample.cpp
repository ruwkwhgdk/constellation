#include "SceneDirectorLibrary.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorCompiler.h"
#include "SceneDirectorPlayer.h"
#include "Engine/Blueprint.h"
#include "EdGraphSchema_K2.h"
#include "K2Node_FunctionEntry.h"
#include "K2Node_FunctionResult.h"
#include "K2Node_CallFunction.h"
#include "K2Node_BreakStruct.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "UObject/SavePackage.h"
#include "Misc/PackageName.h"
namespace
{
bool SaveActionAsset(UObject* A)
{
    FSavePackageArgs Args;Args.TopLevelFlags=RF_Public|RF_Standalone;Args.SaveFlags=SAVE_NoError;
    return UPackage::SavePackage(A->GetOutermost(),A,*FPackageName::LongPackageNameToFilename(A->GetOutermost()->GetName(),FPackageName::GetAssetPackageExtension()),Args);
}
UBlueprint* MakeActionBP(const TCHAR* Name,UFunction* Function,bool bQuest)
{
    const FString Path=FString(TEXT("/Game/SceneDirector/Examples/"))+Name;
    if(auto* Existing=LoadObject<UBlueprint>(nullptr,*(Path+TEXT(".")+Name),nullptr,LOAD_NoWarn))return Existing;
    if(!Function)return nullptr;
    auto* BP=FKismetEditorUtilities::CreateBlueprint(USceneDirectorAction::StaticClass(),CreatePackage(*Path),FName(Name),BPTYPE_Normal);
    auto* Graph=FBlueprintEditorUtils::CreateNewGraph(BP,TEXT("Execute"),UEdGraph::StaticClass(),UEdGraphSchema_K2::StaticClass());
    FBlueprintEditorUtils::AddFunctionGraph(BP,Graph,false,USceneDirectorAction::StaticClass());
    TArray<UK2Node_FunctionEntry*> Entries;Graph->GetNodesOfClass(Entries);
    TArray<UK2Node_FunctionResult*> Results;Graph->GetNodesOfClass(Results);
    if(Entries.Num()!=1||Results.Num()!=1)return nullptr;
    auto* Entry=Entries[0];auto* Result=Results[0];Result->NodePosX=700;
    auto* Call=NewObject<UK2Node_CallFunction>(Graph);Call->SetFromFunction(Function);Graph->AddNode(Call,false,false);Call->CreateNewGuid();Call->PostPlacedNewNode();Call->AllocateDefaultPins();Call->NodePosX=340;
    const auto* Schema=Graph->GetSchema();bool Ok=true;
    auto Link=[&](UEdGraphPin* A,UEdGraphPin* B){if(!A||!B||!Schema->TryCreateConnection(A,B))Ok=false;};
    Entry->FindPinChecked(UEdGraphSchema_K2::PN_Then)->BreakAllPinLinks();
    Link(Entry->FindPin(UEdGraphSchema_K2::PN_Then),Call->GetExecPin());
    Link(Call->GetThenPin(),Result->FindPin(UEdGraphSchema_K2::PN_Execute));
    Link(Call->FindPin(UEdGraphSchema_K2::PN_ReturnValue),Result->FindPin(UEdGraphSchema_K2::PN_ReturnValue));
    if(bQuest)
    {
        auto* Break=NewObject<UK2Node_BreakStruct>(Graph);Break->StructType=FDirectorActionParameters::StaticStruct();Graph->AddNode(Break,false,false);Break->CreateNewGuid();Break->AllocateDefaultPins();Break->NodePosX=40;Break->NodePosY=260;
        Link(Entry->FindPin(TEXT("Parameters")),Break->FindPin(FDirectorActionParameters::StaticStruct()->GetFName()));
        Link(Break->FindPin(TEXT("Identifier")),Call->FindPin(TEXT("QuestID")));
        Link(Entry->FindPin(TEXT("Player")),Call->FindPin(TEXT("WorldContextObject")));
        Schema->TrySetDefaultValue(*Result->FindPinChecked(TEXT("Error")),TEXT("퀘스트 ID와 수락 가능한 상태를 확인하세요."));
    }
    else
    {
        Link(Entry->FindPin(TEXT("Target")),Call->FindPin(TEXT("Target")));
        Link(Entry->FindPin(TEXT("Parameters")),Call->FindPin(TEXT("Parameters")));
        Link(Call->FindPin(TEXT("Error")),Result->FindPin(TEXT("Error")));
    }
    if(!Ok){UE_LOG(LogTemp,Error,TEXT("Action BP pin wiring failed: %s"),Name);return nullptr;}
    FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);FKismetEditorUtilities::CompileBlueprint(BP);
    if(BP->Status==BS_Error||!BP->GeneratedClass)return nullptr;
    FAssetRegistryModule::AssetCreated(BP);BP->MarkPackageDirty();return SaveActionAsset(BP)?BP:nullptr;
}
}
USceneDirectorAsset* USceneDirectorLibrary::CreateActionsExample()
{
    auto* Tag=MakeActionBP(TEXT("BP_ActionSetNPCTag"),USceneDirectorAction::StaticClass()->FindFunctionByName(TEXT("ApplyActorTag")),false);
    auto* QuestClass=LoadObject<UClass>(nullptr,TEXT("/Script/Constellation.QuestSubsystem"));
    auto* Quest=MakeActionBP(TEXT("BP_ActionAcceptQuest"),QuestClass?QuestClass->FindFunctionByName(TEXT("AcceptQuestFor")):nullptr,true);
    if(!Tag||!Quest)return nullptr;
    const TCHAR* Path=TEXT("/Game/SceneDirector/Examples/DA_Actions.DA_Actions");
    if(auto* Existing=LoadObject<USceneDirectorAsset>(nullptr,Path,nullptr,LOAD_NoWarn))return Existing;
    auto* Source=CreateBranchingExample();if(!Source)return nullptr;
    auto* A=DuplicateObject<USceneDirectorAsset>(Source,CreatePackage(TEXT("/Game/SceneDirector/Examples/DA_Actions")),TEXT("DA_Actions"));
    A->SetFlags(RF_Public|RF_Standalone|RF_Transactional);A->EventKey=TEXT("Actions");
    FDirectorActionEntry Entry;Entry.Key=TEXT("SetNPCTag");Entry.ActionClass=Tag->GeneratedClass;A->Actions.Add(Entry);
    Entry=FDirectorActionEntry();Entry.Key=TEXT("AcceptQuest");Entry.ActionClass=Quest->GeneratedClass;A->Actions.Add(Entry);
    // Both answers execute a real BP; no quest/save data is changed by this demonstration.
    for(int32 I:{8,9})
    {
        FDirectorStep S;S.Type=EDirectorNodeType::GameAction;S.ActionKey=TEXT("SetNPCTag");S.ActionTarget=TEXT("Hero");S.ActionParameters.Identifier=I==8?TEXT("HelpAccepted"):TEXT("HelpDeclined");S.NextNodes={A->Steps[I].Id};
        S.EditorPosition=FVector2D(2100,I==8?-160:160);A->Steps[I].EditorPosition.X=2430;
        const FGuid Id=S.Id;A->Steps.Add(S);if(I==8)A->Steps[7].TrueTarget=Id;else A->Steps[7].FalseTarget=Id;
    }
    A->Steps[10].EditorPosition.X=2800;A->Steps[11].EditorPosition.X=3080;
    A->Steps[8].DialogueText=FText::FromString(TEXT("도움 수락 액션이 실행되었어요. 실행기의 Action Results에서 결과를 확인하세요."));
    A->Steps[9].DialogueText=FText::FromString(TEXT("도움 거절 액션이 실행되었어요. 실행기의 Action Results에서 결과를 확인하세요."));
    FString Error;if(!FSceneDirectorCompiler::Compile(*A,Error)){UE_LOG(LogTemp,Error,TEXT("Actions example: %s"),*Error);return nullptr;}
    FAssetRegistryModule::AssetCreated(A);A->MarkPackageDirty();return SaveActionAsset(A)?A:nullptr;
}
