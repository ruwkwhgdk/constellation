#include "SceneDirectorLibrary.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorInteractionComponent.h"
#include "Engine/Blueprint.h"
#include "Engine/SimpleConstructionScript.h"
#include "Engine/SCS_Node.h"
#include "EdGraphSchema_K2.h"
#include "K2Node_Event.h"
#include "K2Node_CallFunction.h"
#include "K2Node_CallParentFunction.h"
#include "K2Node_IfThenElse.h"
#include "K2Node_Self.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "UObject/SavePackage.h"
#include "Misc/PackageName.h"
UBlueprint* USceneDirectorLibrary::CreateStatueInteractionBlueprint(FString& Report)
{
 const FString Path=TEXT("/Game/SceneDirector/Statue/BP_StatueDirector");if(auto* Existing=LoadObject<UBlueprint>(nullptr,*(Path+TEXT(".BP_StatueDirector")),nullptr,LOAD_NoWarn)){Report=TEXT("기존 석상 연결 BP 사용");return Existing;}
 auto* Parent=LoadObject<UBlueprint>(nullptr,TEXT("/Game/Constellation/Environments/School/Blueprints/BP_School_Girl_Statue.BP_School_Girl_Statue"));if(!Parent||!Parent->GeneratedClass){Report=TEXT("원본 석상 BP 없음");return nullptr;}
 auto* Function=Parent->GeneratedClass->FindFunctionByName(TEXT("Interact"));if(!Function){Report=TEXT("원본 Interact 함수 없음");return nullptr;}
 auto* BP=FKismetEditorUtilities::CreateBlueprint(Parent->GeneratedClass,CreatePackage(*Path),TEXT("BP_StatueDirector"),BPTYPE_Normal);
 auto* ComponentNode=BP->SimpleConstructionScript->CreateNode(USceneDirectorInteractionComponent::StaticClass(),TEXT("Ac_SceneDirectorInteraction"));BP->SimpleConstructionScript->AddNode(ComponentNode);
 auto* Component=CastChecked<USceneDirectorInteractionComponent>(ComponentNode->ComponentTemplate);Component->Director=LoadObject<USceneDirectorAsset>(nullptr,TEXT("/Game/SceneDirector/Statue/DA_StatueInteraction.DA_StatueInteraction"));
 if(!Component->Director){Report=TEXT("석상 연출 애셋 없음");return nullptr;}
 auto* G=FBlueprintEditorUtils::FindEventGraph(BP);if(!G){G=FBlueprintEditorUtils::CreateNewGraph(BP,TEXT("EventGraph"),UEdGraph::StaticClass(),UEdGraphSchema_K2::StaticClass());FBlueprintEditorUtils::AddUbergraphPage(BP,G);}
 auto Add=[&](UEdGraphNode* N,int X,int Y){G->AddNode(N,false,false);N->CreateNewGuid();N->PostPlacedNewNode();N->AllocateDefaultPins();N->NodePosX=X;N->NodePosY=Y;};
 auto* Event=NewObject<UK2Node_Event>(G);Event->EventReference.SetExternalMember(TEXT("Interact"),Parent->GeneratedClass);Event->bOverrideFunction=true;Add(Event,0,0);
 auto* Self=NewObject<UK2Node_Self>(G);Add(Self,0,240);
 auto* Route=NewObject<UK2Node_CallFunction>(G);Route->SetFromFunction(USceneDirectorInteractionComponent::StaticClass()->FindFunctionByName(TEXT("RouteInteraction")));Add(Route,300,0);
 auto* Branch=NewObject<UK2Node_IfThenElse>(G);Add(Branch,650,0);
 auto* Original=NewObject<UK2Node_CallParentFunction>(G);Original->SetFromFunction(Function);Add(Original,920,120);
 bool OK=true;auto Link=[&](UEdGraphPin* A,UEdGraphPin* B){if(!A||!B||!G->GetSchema()->TryCreateConnection(A,B))OK=false;};
 Link(Event->FindPin(UEdGraphSchema_K2::PN_Then),Route->GetExecPin());Link(Self->FindPin(UEdGraphSchema_K2::PN_Self),Route->FindPin(TEXT("Owner")));Link(Event->FindPin(TEXT("Interactor")),Route->FindPin(TEXT("Interactor")));Link(Route->GetThenPin(),Branch->GetExecPin());Link(Route->GetReturnValuePin(),Branch->GetConditionPin());Link(Branch->GetElsePin(),Original->GetExecPin());
 for(const FName Name:{FName(TEXT("Interactor")),FName(TEXT("HitComponent"))})Link(Event->FindPin(Name),Original->FindPin(Name));
 if(!OK){Report=TEXT("석상 연결 BP 핀 연결 실패");return nullptr;}FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);FKismetEditorUtilities::CompileBlueprint(BP);if(BP->Status==BS_Error){Report=TEXT("석상 연결 BP 컴파일 실패");return nullptr;}
 FSavePackageArgs Args;Args.TopLevelFlags=RF_Public|RF_Standalone;Args.SaveFlags=SAVE_NoError;if(!UPackage::SavePackage(BP->GetOutermost(),BP,*FPackageName::LongPackageNameToFilename(Path,FPackageName::GetAssetPackageExtension()),Args)){Report=TEXT("석상 연결 BP 저장 실패");return nullptr;}FAssetRegistryModule::AssetCreated(BP);Report=TEXT("원본 BP를 상속한 실행 방식 선택 BP 생성 완료");return BP;
}
void USceneDirectorLibrary::SetDirectorAuthoringOrigin(USceneDirectorAsset* Asset,const FTransform& Origin)
{
 if(!Asset)return;Asset->Modify();Asset->AuthoringOrigin=Origin;for(auto Event:Asset->EventGraphs)SetDirectorAuthoringOrigin(Event,Origin);Asset->MarkPackageDirty();
}

#include "SceneDirectorCompiler.h"
bool USceneDirectorLibrary::UpgradeStatueInteraction(FString& Error)
{
 auto* A=LoadObject<USceneDirectorAsset>(nullptr,TEXT("/Game/SceneDirector/Statue/DA_StatueInteraction.DA_StatueInteraction"));auto* BP=LoadObject<UBlueprint>(nullptr,TEXT("/Game/SceneDirector/Statue/BP_StatueDirector.BP_StatueDirector"));if(!A||!BP){Error=TEXT("석상 애셋 없음");return false;}
 A->Modify();A->bUseInteractionOrigin=true;
 if(!A->BoolVariables.ContainsByPredicate([](const FDirectorBoolEntry& V){return V.Key==TEXT("HasInteracted");})){FDirectorBoolEntry V;V.Key=TEXT("HasInteracted");A->BoolVariables.Add(V);}
 TArray<USceneDirectorAsset*> Events{A};for(auto E:A->EventGraphs)if(E)Events.Add(E);
 for(auto* E:Events)
 {
  E->Modify();FDirectorEventCondition C;C.Key=TEXT("HasInteracted");C.BoolValue=E!=A;E->EntryConditions={C};
  for(auto& S:E->Steps){if(S.Type==EDirectorNodeType::SpawnNPC&&S.Role==TEXT("Heroine"))S.bPlayerStandIn=true;if(S.Type==EDirectorNodeType::Visibility&&!S.bVisible)S.bVisible=true;if(S.Type==EDirectorNodeType::Dialogue){S.bKeepDialogueOpen=true;if(S.SpeakerName.ToString().TrimStartAndEnd().IsEmpty())S.SpeakerName=FText::GetEmpty();if(S.DialogueText.ToString().Contains(TEXT("HP")))S.DialoguePosition=EDirectorDialoguePosition::Center;}}
  if(!E->Steps.ContainsByPredicate([](const FDirectorStep& S){return S.Type==EDirectorNodeType::SetBool&&S.BoolKey==TEXT("HasInteracted");}))
  {
   const auto* Recovery=E->Steps.FindByPredicate([](const FDirectorStep& S){return S.Type==EDirectorNodeType::GameAction&&S.ActionKey==TEXT("RestoreHP");});if(!Recovery||Recovery->NextNodes.Num()!=1){Error=TEXT("회복 경로 연결을 확인하세요.");return false;}
   const auto Return=Recovery->NextNodes[0];FDirectorStep Set;Set.Type=EDirectorNodeType::SetBool;Set.BoolKey=TEXT("HasInteracted");Set.BoolValue=true;Set.NextNodes={Return};
   for(auto& S:E->Steps)for(auto& Next:S.NextNodes)if(Next==Return)Next=Set.Id;E->Steps.Add(Set);
  }
  E->SyncVariables();if(!FSceneDirectorCompiler::Compile(*E,Error))return false;ArrangeDirectorGraph(E);
 }
 for(auto* N:BP->SimpleConstructionScript->GetAllNodes())if(N->ComponentTemplate->IsA<USceneDirectorInteractionComponent>())N->SetVariableName(TEXT("Ac_SceneDirectorInteraction"));
 FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);FKismetEditorUtilities::CompileBlueprint(BP);if(BP->Status==BS_Error){Error=TEXT("석상 BP 컴파일 오류");return false;}
 for(UObject* O:TArray<UObject*>{A,BP}){FSavePackageArgs Args;Args.TopLevelFlags=RF_Public|RF_Standalone;Args.SaveFlags=SAVE_NoError;if(!UPackage::SavePackage(O->GetOutermost(),O,*FPackageName::LongPackageNameToFilename(O->GetOutermost()->GetName(),FPackageName::GetAssetPackageExtension()),Args))return false;}
 return true;
}
