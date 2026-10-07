#include "SceneDirectorLibrary.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorNodeTypes.h"
#include "SceneDirectorCompiler.h"
#include "SceneDirectorSequence.h"
#include "LevelSequence.h"
#include "MovieScene.h"
#include "MovieSceneBindingReferences.h"
#include "Bindings/MovieSceneSpawnableActorBinding.h"
#include "Sections/MovieSceneEventTriggerSection.h"
#include "Tracks/MovieSceneEventTrack.h"
#include "K2Node_CustomEvent.h"
#include "K2Node_CallFunction.h"
#include "EdGraphSchema_K2.h"
#include "Engine/DataTable.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Misc/PackageName.h"
#include "UObject/SavePackage.h"
namespace
{
struct FSchoolGraph
{
 USceneDirectorAsset* A;
 FGuid Add(FDirectorStep S){S.Id=FGuid::NewGuid();A->Steps.Add(S);return S.Id;}
 void Link(FGuid From,FGuid To){A->Steps.FindByPredicate([&](const FDirectorStep& S){return S.Id==From;})->NextNodes.Add(To);}
 FGuid At(FGuid Parent,int Frame,FDirectorStep S){if(Frame>0){FDirectorStep W;W.Type=EDirectorNodeType::Wait;W.Duration=Frame/30.f;auto ID=Add(W);Link(Parent,ID);Parent=ID;}auto ID=Add(S);Link(Parent,ID);return ID;}
};
AActor* SchoolTemplate(ULevelSequence* S,FGuid ID)
{
 if(auto* T=S->GetMovieScene()->FindSpawnable(ID))return Cast<AActor>(T->GetObjectTemplate());
 if(auto* Refs=S->GetBindingReferences())for(const auto& R:Refs->GetReferences(ID))if(auto* T=Cast<UMovieSceneSpawnableActorBinding>(R.CustomBinding))return Cast<AActor>(T->GetObjectTemplate());return nullptr;
}
struct FSchoolEvent{int Frame;FGuid Binding;FName Operation;TMap<FName,FString> Params;};
}
USceneDirectorAsset* USceneDirectorLibrary::CreateSchoolPerformance(ULevelSequence* Source,ULevelSequence* Visual,const TMap<FString,AActor*>& Actors,const FString& AssetPath,FString& Report)
{
 auto Fail=[&](FString E)->USceneDirectorAsset*{Report=E;return nullptr;};
 if(!Source||!Visual||Source==Visual)return Fail(TEXT("원본과 별도의 시각 레이어 사본이 필요합니다."));
 if(FindPackage(nullptr,*AssetPath))return Fail(TEXT("이미 열린 대상 애셋입니다. 기존 편집 내용을 덮어쓰지 않습니다."));
 auto* ActionClass=FindObject<UClass>(nullptr,TEXT("/Script/Constellation.SceneSchoolAction"));if(!ActionClass)return Fail(TEXT("게임 액션 클래스 없음"));
 auto* A=NewObject<USceneDirectorAsset>();FSchoolGraph G{A};A->EventKey=FName(*Source->GetName());A->ImportedFrom=Source;
 FDirectorActionEntry Action;Action.Key=TEXT("SchoolGameAction");Action.ActionClass=ActionClass;A->Actions.Add(Action);
 FDirectorStep Start;Start.Type=EDirectorNodeType::Start;FGuid Setup=G.Add(Start);
 FDirectorStep Clip;Clip.Type=EDirectorNodeType::Sequence;Clip.SourceSequence=Visual;DirectorSequence::RefreshRoles(Clip);
 TMap<FGuid,FName> Keys;FName HeroKey;TArray<FGuid> SetupEnds;
 for(auto& Role:Clip.SequenceRoles)
 {
  auto* Template=SchoolTemplate(Source,Role.Binding);AActor* Actor=Actors.FindRef(Role.Binding.ToString());const bool Hero=Role.Label.Contains(TEXT("npc_player"))||Role.Label.Contains(TEXT("BP_NPC_Player_Heroine"));
  if(Template&&!Hero&&!Role.SourceClass->IsChildOf(ACameraActor::StaticClass()))continue;
  AActor* Model=Template?Template:Actor;if(!Model)return Fail(TEXT("원본 Actor 연결 누락: ")+Role.Label);
  const FName Key=Hero?FName(TEXT("Heroine")):FName(*Role.Label.Replace(TEXT(" "),TEXT("_")));Keys.Add(Role.Binding,Key);if(Hero)HeroKey=Key;
  if(Actor){FDirectorObjectEntry O;O.Key=Key;O.ActorClass=Actor->GetClass();O.ActorTag=FName(*(TEXT("SceneDirector.School.")+Actor->GetName()));A->Objects.Add(O);}
  const FTransform Initial=Model->GetAttachParentActor()?Model->GetRootComponent()->GetRelativeTransform():Model->GetActorTransform();
  if(Model->IsA<ACameraActor>())
  {
   Role.Target=EDirectorSequenceTarget::Camera;Role.Key=Key;FDirectorCameraEntry C;C.Key=Key;C.Transform=Initial;C.ImportedTemplate=DuplicateObject<AActor>(Model,A);C.ImportedTemplate->DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);if(Actor)C.ObjectKey=Key;C.FieldOfView=CastChecked<ACameraActor>(Model)->GetCameraComponent()->FieldOfView;A->Cameras.Add(C);
   FDirectorStep Init;Init.Type=EDirectorNodeType::CameraMove;Init.CameraKey=Key;Init.bActivateCamera=false;Init.bWaitForCompletion=true;Init.Duration=1.f/30;Init.Destination.Value=Initial.GetLocation();Init.Rotation.Value=Initial.Rotator().Euler();auto ID=G.Add(Init);G.Link(Setup,ID);Setup=ID;
  }
  else
  {
   Role.Target=EDirectorSequenceTarget::NPC;Role.Key=Key;FDirectorStep Bind;Bind.Type=Template?EDirectorNodeType::SpawnNPC:EDirectorNodeType::BindNPC;Bind.Role=Key;Bind.ActorClass=Model->GetClass();Bind.Transform=Initial;Bind.bPlayerStandIn=Hero;
   if(Template){Bind.ImportedTemplate=DuplicateObject<AActor>(Template,A);Bind.ImportedTemplate->DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);}
   else {Bind.ActorSource=EDirectorActorSource::Object;Bind.ObjectKey=Key;}
   auto ID=G.Add(Bind);G.Link(Setup,ID);Setup=ID;
  }
 }
 if(HeroKey.IsNone())return Fail(TEXT("플레이어 대역을 찾지 못했습니다."));
 FDirectorStep Mode;Mode.Type=EDirectorNodeType::CinematicMode;Mode.bHidePlayer=true;auto ModeID=G.Add(Mode);G.Link(Setup,ModeID);Setup=ModeID;
 TArray<FSchoolEvent> Events;FString Error;
 auto Collect=[&](const TArray<UMovieSceneTrack*>& Tracks,FGuid Binding)
 {
  for(auto* T:Tracks)if(auto* ET=Cast<UMovieSceneEventTrack>(T))for(auto* Base:ET->GetAllSections())
  {
   auto* Section=Cast<UMovieSceneEventTriggerSection>(Base);if(!Section){Error=TEXT("반복 이벤트 트랙은 수동 이관이 필요합니다.");return;}
   auto Data=Section->EventChannel.GetData();for(int I=0;I<Data.GetTimes().Num();++I)
   {
    const auto& V=Data.GetValues()[I];auto* E=Cast<UK2Node_CustomEvent>(V.WeakEndpoint.Get());auto* Then=E?E->FindPin(UEdGraphSchema_K2::PN_Then):nullptr;auto* Call=Then&&Then->LinkedTo.Num()==1?Cast<UK2Node_CallFunction>(Then->LinkedTo[0]->GetOwningNode()):nullptr;
    if(!Call){Error=TEXT("단일 함수 호출 외의 원본 이벤트가 있습니다.");return;}
    FSchoolEvent Event;Event.Frame=FMath::RoundToInt(Data.GetTimes()[I].Value*30/Source->GetMovieScene()->GetTickResolution().AsDecimal());Event.Binding=Binding;Event.Operation=Call->FunctionReference.GetMemberName();for(const auto& P:V.PayloadVariables)Event.Params.Add(P.Key,P.Value.Value);Events.Add(Event);
   }
  }
 };
 Collect(Source->GetMovieScene()->GetTracks(),FGuid());for(const auto& B:static_cast<const UMovieScene*>(Source->GetMovieScene())->GetBindings())Collect(B.GetTracks(),B.GetObjectGuid());if(!Error.IsEmpty())return Fail(Error);
 // Remove only event tracks from the working copy; every visual channel remains available in the retained layer.
 auto RemoveEvents=[&](const TArray<UMovieSceneTrack*>& In){const auto Tracks=In;for(auto* T:Tracks)if(T->IsA<UMovieSceneEventTrack>())Visual->GetMovieScene()->RemoveTrack(*T);};
 RemoveEvents(Visual->GetMovieScene()->GetTracks());for(const auto& B:static_cast<const UMovieScene*>(Visual->GetMovieScene())->GetBindings())RemoveEvents(B.GetTracks());
 Visual->SetDirectorBlueprint(nullptr);Visual->MarkPackageDirty();TArray<FGuid> Ends;Ends.Add(G.At(Setup,0,Clip));
 Events.Sort([](const FSchoolEvent& L,const FSchoolEvent& R){return L.Frame<R.Frame;});FGuid DialogueParent=Setup,ActionParent=Setup;int PreviousDialogueEnd=0,PreviousActionFrame=0;
 auto* Strings=LoadObject<UDataTable>(nullptr,TEXT("/Game/Constellation/Gameplay/Sequences/Data/DT_SequenceStringData.DT_SequenceStringData"));
 for(const auto& E:Events)
 {
  FDirectorStep S;S.Type=EDirectorNodeType::GameAction;S.ActionKey=Action.Key;S.ActionTarget=Keys.FindRef(E.Binding);FName Op=E.Operation;
  if(Op==TEXT("Pause Sequence and Set Dialogue UI"))
  {
   S.Type=EDirectorNodeType::Dialogue;S.Role=HeroKey;S.Duration=1.f/30;S.DialogueAdvance=EDirectorDialogueAdvance::Click;S.bKeepDialogueOpen=!E.Params.FindRef(TEXT("IsRemoveUIFinished")).ToBool();S.SpeakerName=FText::GetEmpty();
   const auto* Row=Strings?Strings->FindRowUnchecked(FName(*E.Params.FindRef(TEXT("DialogueKey")))):nullptr;if(!Row)return Fail(TEXT("원본 대사 행 없음"));for(TFieldIterator<FTextProperty> It(Strings->GetRowStruct());It;++It){S.DialogueText=It->GetPropertyValue_InContainer(Row);break;}
   if(S.DialogueText.IsEmpty())return Fail(TEXT("원본 대사 없음"));DialogueParent=G.At(DialogueParent,E.Frame-PreviousDialogueEnd,S);PreviousDialogueEnd=E.Frame+1;continue;
  }
  if(Op==TEXT("Fade Out")||Op==TEXT("Fade In")){S.Type=EDirectorNodeType::Fade;S.Duration=FMath::Max(1.f/30,FCString::Atof(*E.Params.FindRef(TEXT("FadeDuration"))));S.FadeFrom=Op==TEXT("Fade Out")?0:1;S.FadeTo=1-S.FadeFrom;}
  else if(Op==TEXT("Save Player Position And Rotation")){S.ActionParameters.Identifier=TEXT("CapturePlayerPose");S.ActionTarget=HeroKey;}
  else if(Op==TEXT("AdvanceQuestOnFinish")){if(E.Params.FindRef(TEXT("QuestID"))!=TEXT("MQ1_ExitSchool")||E.Params.FindRef(TEXT("bAdvanceInnerProgress")).ToBool())return Fail(TEXT("지원되지 않는 퀘스트 이벤트"));S.ActionParameters.Identifier=TEXT("AdvanceQuest");}
  else if(Op==TEXT("Activate NPC"))S.ActionParameters.Identifier=TEXT("ActivateNPC");
  else if(Op==TEXT("Deactivate NPC")){if(S.ActionTarget==HeroKey)continue;S.ActionParameters.Identifier=TEXT("DeactivateNPC");}
  else if(Op==TEXT("Deactivate Actor"))S.ActionParameters.Identifier=TEXT("DeactivateActor");
  else if(Op==TEXT("Set Actor Hidden In Game"))S.ActionParameters.Identifier=TEXT("HideActor");
  else if(Op==TEXT("Resize NPC Capsule Collision")){S.ActionParameters.Identifier=TEXT("ResizeCapsule");S.ActionParameters.Value=FCString::Atof(*E.Params.FindRef(TEXT("HalfHeight")));S.ActionParameters.Amount=FCString::Atoi(*E.Params.FindRef(TEXT("Radius")));}
  else if(Op==TEXT("TriggerAll"))S.ActionParameters.Identifier=TEXT("TriggerCache");
  else return Fail(TEXT("미지원 게임 이벤트: ")+Op.ToString());
  if(S.Type==EDirectorNodeType::GameAction&&S.ActionParameters.Identifier!=TEXT("AdvanceQuest")&&S.ActionTarget.IsNone())return Fail(TEXT("게임 이벤트 대상 연결 누락: ")+Op.ToString());
  if(S.Type==EDirectorNodeType::GameAction){ActionParent=G.At(ActionParent,E.Frame-PreviousActionFrame,S);PreviousActionFrame=E.Frame;}else Ends.Add(G.At(Setup,E.Frame,S));
 }
 if(DialogueParent!=Setup)Ends.Add(DialogueParent);if(ActionParent!=Setup)Ends.Add(ActionParent);
 FDirectorStep Return;Return.Type=EDirectorNodeType::GameplayReturn;Return.Duration=1.5;auto ReturnID=G.Add(Return);for(auto E:Ends)G.Link(E,ReturnID);FDirectorStep End;End.Type=EDirectorNodeType::End;auto EndID=G.Add(End);G.Link(ReturnID,EndID);
 A->ImportReport=TEXT("원본 보존. 대사·페이드·게임 액션·제어권 복귀는 노드화. 부착·카메라 흔들림·원본 애니메이션/키는 이벤트 없는 시각 레이어 사본으로 유지.");ArrangeDirectorGraph(A);
 if(!FSceneDirectorCompiler::Compile(*A,Error))return Fail(Error);
 auto* Package=CreatePackage(*AssetPath);auto* Result=DuplicateObject<USceneDirectorAsset>(A,Package,*FPackageName::GetLongPackageAssetName(AssetPath));Result->SetFlags(RF_Public|RF_Standalone);FAssetRegistryModule::AssetCreated(Result);Result->MarkPackageDirty();Report=Result->ImportReport;return Result;
}


bool USceneDirectorLibrary::SetGameplayReturnDuration(USceneDirectorAsset* A,float Seconds,FString& Error){if(!A||!FMath::IsFinite(Seconds)||Seconds<1.f/30)return false;A->Modify();for(auto& S:A->Steps)if(DirectorNodes::IsReturn(S.Type))S.Duration=Seconds;return FSceneDirectorCompiler::Compile(*A,Error);}
