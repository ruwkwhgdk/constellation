#include "SceneDirectorLibrary.h"
#include "Engine/Blueprint.h"
#include "EdGraphSchema_K2.h"
#include "K2Node_CallFunction.h"
#include "K2Node_CustomEvent.h"
#include "K2Node_CallDelegate.h"
#include "K2Node_VariableGet.h"
#include "K2Node_VariableSet.h"
#include "K2Node_Self.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "LevelSequence.h"
#include "MovieScene.h"
#include "MovieSceneBindingReferences.h"
#include "Sections/MovieSceneEventTriggerSection.h"
#include "Tracks/MovieSceneEventTrack.h"
bool USceneDirectorLibrary::ConnectGameSignals(UBlueprint* BP,const FString& Kind,FString& Error)
{
 if(!BP){Error=TEXT("Blueprint 없음");return false;}auto* Lib=FindObject<UClass>(nullptr,TEXT("/Script/Constellation.SceneGameLibrary"));if(!Lib){Error=TEXT("게임 연결 클래스 없음");return false;}
 auto* G=FBlueprintEditorUtils::FindEventGraph(BP);if(!G){Error=TEXT("이벤트 그래프 없음");return false;}
 const FString Marker=TEXT("SceneDirector.Signal.")+Kind;
 for(UEdGraphNode* N:G->Nodes)if(N->NodeComment==Marker){Error=TEXT("이미 연결됨");return true;}
 TArray<UEdGraphNode*> Targets;UEdGraphPin* Key=nullptr;
 for(UEdGraphNode* N:G->Nodes)
 {
  if(Kind==TEXT("Ready"))if(auto* Set=Cast<UK2Node_VariableSet>(N);Set&&Set->VariableReference.GetMemberName()==TEXT("Ref_PlayerCharacter"))Targets.Add(N);
  if(Kind==TEXT("Start"))if(auto* Call=Cast<UK2Node_CallFunction>(N);Call&&Call->FunctionReference.GetMemberName()==TEXT("BattleManager Battle Start"))Targets.Add(N);
  if(Kind==TEXT("End"))
  {if(auto* Call=Cast<UK2Node_CallDelegate>(N);Call&&Call->DelegateReference.GetMemberName()==TEXT("OnBattleEnded"))Targets.Add(N);if(auto* E=Cast<UK2Node_CustomEvent>(N);E&&E->CustomFunctionName==TEXT("BattleManager Battle End"))Key=E->FindPin(TEXT("BattleZoneKey"));}
 }
 if(Targets.IsEmpty()||(Kind==TEXT("End")&&!Key)){Error=TEXT("예상한 실제 게임 연결 지점 없음");return false;}
 auto* Function=Lib->FindFunctionByName(Kind==TEXT("Ready")?TEXT("NotifyGameplayUIReady"):Kind==TEXT("Start")?TEXT("NotifyBattleStarted"):TEXT("NotifyBattleEnded"));if(!Function)return false;
 BP->Modify();G->Modify();bool OK=true;
 for(auto* Target:Targets)
 {
  auto Add=[&](UEdGraphNode* N){G->AddNode(N,false,false);N->CreateNewGuid();N->PostPlacedNewNode();N->AllocateDefaultPins();N->NodePosX=Target->NodePosX+280;N->NodePosY=Target->NodePosY;};
  auto* Call=NewObject<UK2Node_CallFunction>(G);Call->SetFromFunction(Function);Add(Call);Call->NodeComment=Marker;
  auto* Self=NewObject<UK2Node_Self>(G);Add(Self);Self->NodePosY+=170;
  auto Link=[&](UEdGraphPin* A,UEdGraphPin* B){if(!A||!B||!G->GetSchema()->TryCreateConnection(A,B))OK=false;};
  Link(Self->FindPin(UEdGraphSchema_K2::PN_Self),Call->FindPin(TEXT("WorldContextObject")));
  if(Kind==TEXT("Start")){auto* Get=NewObject<UK2Node_VariableGet>(G);Get->VariableReference.SetSelfMember(TEXT("BattleZoneKey"));Add(Get);Get->NodePosY+=270;Link(Get->FindPin(TEXT("BattleZoneKey")),Call->FindPin(TEXT("BattleZoneKey")));}
  if(Kind==TEXT("End"))Link(Key,Call->FindPin(TEXT("BattleZoneKey")));
  auto* Then=Target->FindPin(UEdGraphSchema_K2::PN_Then);if(!Then){OK=false;continue;}auto Links=Then->LinkedTo;Then->BreakAllPinLinks();Link(Then,Call->GetExecPin());for(auto* Next:Links)Link(Call->GetThenPin(),Next);
 }
 if(!OK){Error=TEXT("신호 연결 핀 오류");return false;}FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);FKismetEditorUtilities::CompileBlueprint(BP);if(BP->Status==BS_Error){Error=TEXT("신호 연결 컴파일 오류");return false;}BP->MarkPackageDirty();return true;
}
FString USceneDirectorLibrary::InspectLegacySequence(ULevelSequence* S,UWorld* World)
{
 if(!S)return TEXT("No source");FString Out;auto* M=S->GetMovieScene();const double Rate=M->GetTickResolution().AsDecimal();
 auto Tracks=[&](const TArray<UMovieSceneTrack*>& List,const FString& Binding)
 {
  for(auto* T:List)if(auto* Events=Cast<UMovieSceneEventTrack>(T))for(auto* Sec:Events->GetAllSections())if(auto* E=Cast<UMovieSceneEventTriggerSection>(Sec))
  {auto Data=E->EventChannel.GetData();for(int32 I=0;I<Data.GetTimes().Num();++I){const auto& V=Data.GetValues()[I];auto* Endpoint=Cast<UK2Node_CustomEvent>(V.WeakEndpoint.Get());Out+=FString::Printf(TEXT("EVENT %.6f | %s | %s | bound=%s\n"),Data.GetTimes()[I].Value/Rate,*Binding,Endpoint?*Endpoint->CustomFunctionName.ToString():*GetNameSafe(V.Ptrs.Function),*V.BoundObjectPinName.ToString());for(const auto& P:V.PayloadVariables)Out+=TEXT("  payload ")+P.Key.ToString()+TEXT("=")+P.Value.Value+TEXT(" object=")+P.Value.ObjectValue.ToString()+TEXT("\n");if(Endpoint)if(auto* Then=Endpoint->FindPin(UEdGraphSchema_K2::PN_Then))for(auto* Next:Then->LinkedTo)if(auto* Call=Cast<UK2Node_CallFunction>(Next->GetOwningNode())){Out+=TEXT("  call ")+Call->FunctionReference.GetMemberName().ToString()+TEXT("\n");for(auto* Pin:Call->Pins)if(Pin->Direction==EGPD_Input&&Pin->LinkedTo.IsEmpty())Out+=TEXT("    ")+Pin->PinName.ToString()+TEXT("=")+Pin->GetDefaultAsString()+TEXT("\n");}}}
 };
 Tracks(M->GetTracks(),TEXT("MASTER"));
 for(const auto& B:static_cast<const UMovieScene*>(M)->GetBindings())
 {Out+=TEXT("BIND ")+B.GetObjectGuid().ToString()+TEXT(" ")+(M->FindPossessable(B.GetObjectGuid())?M->FindPossessable(B.GetObjectGuid())->GetName():B.GetName())+TEXT("\n");if(auto* Refs=S->GetBindingReferences())for(const auto& Ref:Refs->GetReferences(B.GetObjectGuid())){TStringBuilder<512> L;Ref.Locator.ToString(L);Out+=FString(TEXT("  locator "))+L.ToString()+TEXT(" custom=")+GetNameSafe(Ref.CustomBinding)+TEXT("\n");}TArray<UObject*,TInlineAllocator<1>> Objects;S->LocateBoundObjects(B.GetObjectGuid(),World,Objects);for(auto* O:Objects)Out+=TEXT("  object ")+O->GetPathName()+TEXT("\n");Tracks(B.GetTracks(),B.GetName());}
 return Out;
}

#include "K2Node_IfThenElse.h"
#include "K2Node_Event.h"
#include "Engine/LevelScriptBlueprint.h"
#include "Engine/Level.h"
bool USceneDirectorLibrary::ConnectMappedInteraction(UBlueprint* BP,FString& Error)
{
 auto* G=BP?FBlueprintEditorUtils::FindEventGraph(BP):nullptr;auto* Lib=FindObject<UClass>(nullptr,TEXT("/Script/Constellation.SceneGameLibrary"));auto* F=Lib?Lib->FindFunctionByName(TEXT("RouteMappedInteraction")):nullptr;if(!G||!F){Error=TEXT("상호작용 그래프/게임 연결 함수 없음");return false;}
 TArray<TPair<UEdGraphNode*,bool>> Entries;
 for(UEdGraphNode* N:G->Nodes){if(auto* E=Cast<UK2Node_Event>(N);E&&E->EventReference.GetMemberName()==TEXT("Interact"))Entries.Add({N,false});if(auto* C=Cast<UK2Node_CustomEvent>(N);C&&C->CustomFunctionName==TEXT("Event After UI"))Entries.Add({N,true});}
 if(Entries.Num()!=2){Error=TEXT("원본 상호작용 진입점이 변경되었습니다.");return false;}BP->Modify();G->Modify();
 for(const auto& Entry:Entries)
 {
  const FString Marker=Entry.Value?TEXT("SceneDirector.Interaction.AfterUI"):TEXT("SceneDirector.Interaction.Preflight");bool Exists=false;for(UEdGraphNode* N:G->Nodes)Exists|=N->NodeComment==Marker;if(Exists)continue;
  auto Add=[&](UEdGraphNode* N){G->AddNode(N,false,false);N->CreateNewGuid();N->PostPlacedNewNode();N->AllocateDefaultPins();N->NodePosX=Entry.Key->NodePosX+250;N->NodePosY=Entry.Key->NodePosY+150;};
  auto* Call=NewObject<UK2Node_CallFunction>(G);Call->SetFromFunction(F);Add(Call);Call->NodeComment=Marker;Call->FindPin(TEXT("bAfterUI"))->DefaultValue=Entry.Value?TEXT("true"):TEXT("false");
  auto* Self=NewObject<UK2Node_Self>(G);Add(Self);auto* Branch=NewObject<UK2Node_IfThenElse>(G);Add(Branch);Branch->NodePosX+=300;
  bool OK=true;auto Link=[&](UEdGraphPin* A,UEdGraphPin* B){if(!A||!B||!G->GetSchema()->TryCreateConnection(A,B))OK=false;};
  auto* Then=Entry.Key->FindPin(UEdGraphSchema_K2::PN_Then);auto Next=Then->LinkedTo;Then->BreakAllPinLinks();Link(Then,Call->GetExecPin());Link(Self->FindPin(UEdGraphSchema_K2::PN_Self),Call->FindPin(TEXT("Source")));Link(Call->GetReturnValuePin(),Branch->GetConditionPin());Link(Call->GetThenPin(),Branch->GetExecPin());for(auto* N:Next)Link(Branch->GetElsePin(),N);
  if(!OK){Error=TEXT("상호작용 연결 실패");return false;}
 }
 FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);FKismetEditorUtilities::CompileBlueprint(BP);if(BP->Status==BS_Error){Error=TEXT("상호작용 BP 컴파일 오류");return false;}BP->MarkPackageDirty();return true;
}
bool USceneDirectorLibrary::DisconnectLegacyVolume(UWorld* W,ULevelSequence* Source,FString& Error)
{
 auto* BP=W&&W->PersistentLevel?W->PersistentLevel->GetLevelScriptBlueprint():nullptr;auto* G=BP?FBlueprintEditorUtils::FindEventGraph(BP):nullptr;if(!G)return false;
 for(UEdGraphNode* N:G->Nodes)if(auto* C=Cast<UK2Node_CallFunction>(N);C&&C->FunctionReference.GetMemberName()==TEXT("CreateLevelSequencePlayer"))if(auto* Pin=C->FindPin(TEXT("LevelSequence"));Pin&&Pin->DefaultObject==Source)
 {BP->Modify();G->Modify();C->GetExecPin()->BreakAllPinLinks();C->NodeComment=TEXT("SceneDirector.VolumeMigrated: original retained disconnected");FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);FKismetEditorUtilities::CompileBlueprint(BP);if(BP->Status==BS_Error){Error=TEXT("레벨 BP 컴파일 실패");return false;}BP->MarkPackageDirty();return true;}
 Error=TEXT("이관할 영역의 원본 재생 노드 없음");return false;
}
