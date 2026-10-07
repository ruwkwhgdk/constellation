#include "SceneDirectorLibrary.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorStatueAction.h"
#include "SceneDirectorCompiler.h"
#include "LevelSequence.h"
#include "MovieScene.h"
#include "EngineUtils.h"
#include "Engine/Blueprint.h"
#include "Engine/DataTable.h"
#include "CineCameraActor.h"
#include "CineCameraComponent.h"
#include "Tracks/MovieScene3DTransformTrack.h"
#include "Tracks/MovieSceneSkeletalAnimationTrack.h"
#include "Sections/MovieSceneSkeletalAnimationSection.h"
#include "Channels/MovieSceneDoubleChannel.h"
#include "Animation/AnimSequence.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "UObject/SavePackage.h"
#include "Misc/PackageName.h"
namespace
{
const FString StatueDir=TEXT("/Game/Constellation/Gameplay/Sequences/LevelSequences/LS_AbandonedSchool_Checkpoint_Event_");
ULevelSequence* StatueSource(const TCHAR* Suffix){const FString P=StatueDir+Suffix;return LoadObject<ULevelSequence>(nullptr,*(P+TEXT(".")+FPackageName::GetLongPackageAssetName(P)));}
struct FStatueGraph
{
 USceneDirectorAsset* A;FGuid Setup,End;int Lane=0;
 FGuid Add(FDirectorStep S){S.Id=FGuid::NewGuid();S.EditorPosition=FVector2D(700+Lane%3*330,Lane/3*210);++Lane;A->Steps.Add(S);return S.Id;}
 FDirectorStep& Get(FGuid ID){return *A->Steps.FindByPredicate([ID](const FDirectorStep& S){return S.Id==ID;});}
 void Link(FGuid From,FGuid To){Get(From).NextNodes.Add(To);}
 FGuid At(FGuid Parent,int Frame,FDirectorStep S){if(Frame>0){FDirectorStep W;W.Type=EDirectorNodeType::Wait;W.Duration=Frame/30.f;const auto ID=Add(W);Link(Parent,ID);Parent=ID;}const auto ID=Add(S);Link(Parent,ID);return ID;}
};
FText StatueText(int N)
{
 auto* Table=LoadObject<UDataTable>(nullptr,TEXT("/Game/Constellation/Gameplay/Sequences/Data/DT_SequenceStringData.DT_SequenceStringData"));
 if(!Table)return FText();auto* Row=Table->FindRowUnchecked(FName(*FString::Printf(TEXT("AbandonedSchool_Sequence_Savepoint_%d"),N)));
 if(!Row)return FText();for(TFieldIterator<FTextProperty> It(Table->GetRowStruct());It;++It)return It->GetPropertyValue_InContainer(Row);return FText();
}
// Preserve individual source channels and tangents; only convert time units and local translation.
FDirectorStep StatueMotion(ULevelSequence* Source,bool Camera,FVector Origin)
{
 FDirectorStep S;S.Type=Camera?EDirectorNodeType::CameraMove:EDirectorNodeType::CharacterMove;S.Role=TEXT("Heroine");S.CameraKey=TEXT("StatueCamera");S.bUseMotionPath=true;S.bPlayMoveAnimation=false;S.bActivateCamera=Camera;
 auto* M=Source->GetMovieScene();const double Rate=M->GetTickResolution().AsDecimal(),Scale=30./Rate;const int Last=FMath::RoundToInt(M->GetPlaybackRange().GetUpperBoundValue().Value*Scale);
 for(const auto& B:static_cast<const UMovieScene*>(M)->GetBindings())if(M->FindPossessable(B.GetObjectGuid()) && M->FindPossessable(B.GetObjectGuid())->GetName().Contains(Camera?TEXT("CineCameraActor"):TEXT("BP_NPC_Player_Heroine")))
 for(auto* T:B.GetTracks())if(auto* Track=Cast<UMovieScene3DTransformTrack>(T))
 {
  auto Channels=Track->GetAllSections()[0]->GetChannelProxy().GetChannels<FMovieSceneDoubleChannel>();TArray<FMovieSceneDoubleChannel> Copies;TSet<int> Times{0,Last};
  for(int Axis=0;Axis<9;++Axis){auto Copy=*Channels[Axis];TArray<FFrameNumber> Frames;TArray<FMovieSceneDoubleValue> Values;auto Data=Copy.GetData();for(int K=0;K<Data.GetTimes().Num();++K){const int F=FMath::RoundToInt(Data.GetTimes()[K].Value*Scale);Frames.Add(F);auto V=Data.GetValues()[K];V.Tangent.ArriveTangent/=Scale;V.Tangent.LeaveTangent/=Scale;if(Axis<3)V.Value+=Origin[Axis];Values.Add(V);Times.Add(F);}if(Axis<3&&Copy.GetDefault().IsSet())Copy.SetDefault(Copy.GetDefault().GetValue()+Origin[Axis]);Copy.Set(Frames,Values);Copy.SetTickResolution(FFrameRate(30,1));Copies.Add(Copy);}
  auto Ordered=Times.Array();Ordered.Sort();for(int Frame:Ordered){FDirectorMotionPoint P;P.Time=Frame/30.;P.Interpolation=EDirectorPathInterpolation::Original;P.OriginalValues.SetNum(9);for(int Axis=0;Axis<9;++Axis){double V=Axis<6?0:1;Copies[Axis].Evaluate(FFrameTime(Frame),V);if(Axis<3)P.Position[Axis]=V;else if(Axis<6)P.Rotation[Axis-3]=V;else P.Scale[Axis-6]=V;auto Data=Copies[Axis].GetData();int K=Data.GetTimes().Find(Frame);if(K!=INDEX_NONE){P.OriginalMask|=1<<Axis;P.OriginalValues[Axis]=Data.GetValues()[K];}else{P.OriginalValues[Axis]=FMovieSceneDoubleValue(V);P.OriginalValues[Axis].InterpMode=RCIM_Constant;if(Frame==0)P.OriginalMask|=1<<Axis;}}P.OriginalPosition=P.Position;P.OriginalRotation=P.Rotation;P.OriginalScale=P.Scale;S.MotionPoints.Add(P);}return S;
 }
 return S;
}
void StatueAnimations(FStatueGraph& G,FGuid Parent,ULevelSequence* Source,TArray<FGuid>& Ends)
{
 const double Rate=Source->GetMovieScene()->GetTickResolution().AsDecimal();
 for(const auto& B:static_cast<const UMovieScene*>(Source->GetMovieScene())->GetBindings())for(auto* T:B.GetTracks())if(auto* Track=Cast<UMovieSceneSkeletalAnimationTrack>(T))for(auto* Base:Track->GetAllSections())
 {
 auto* S=CastChecked<UMovieSceneSkeletalAnimationSection>(Base);FDirectorStep Step;Step.Type=EDirectorNodeType::Animation;Step.Role=TEXT("Heroine");Step.Animation=Cast<UAnimSequence>(S->Params.Animation);Step.bForceCustomAnimation=S->Params.bForceCustomMode;Step.Duration=(S->GetExclusiveEndFrame().Value-S->GetInclusiveStartFrame().Value)/Rate;Step.bExplicitAnimationRate=true;Step.AnimationRate=S->Params.PlayRate.AsFixedPlayRate();Step.AnimationStartOffset=S->Params.StartFrameOffset.Value/Rate;Step.AnimationEndOffset=S->Params.EndFrameOffset.Value/Rate;Step.AnimationFirstOffset=S->Params.FirstLoopStartFrameOffset.Value/Rate;Step.bAnimationReverse=S->Params.bReverse;Step.AnimationWeight=S->Params.Weight.GetDefault().Get(1.f);Step.AnimationBlendIn=S->Easing.GetEaseInDuration()/Rate;Step.AnimationBlendOut=S->Easing.GetEaseOutDuration()/Rate;Step.bAllowAnimationBlend=true;
 if(auto* E=Cast<UMovieSceneBuiltInEasingFunction>(S->Easing.EaseIn.GetObject()))Step.AnimationEaseIn=E->Type;if(auto* E=Cast<UMovieSceneBuiltInEasingFunction>(S->Easing.EaseOut.GetObject()))Step.AnimationEaseOut=E->Type;
 Ends.Add(G.At(Parent,FMath::RoundToInt(S->GetInclusiveStartFrame().Value*30/Rate),Step));
 }
}
FDirectorStep StatueDialogue(int N){FDirectorStep S;S.Type=EDirectorNodeType::Dialogue;S.Role=TEXT("Heroine");S.SpeakerName=FText::FromString(TEXT(" "));S.DialogueText=StatueText(N);S.DialogueAdvance=EDirectorDialogueAdvance::Click;S.Duration=1.f/30;return S;}
USceneDirectorAsset* BuildStatue(UObject* Outer,bool Repeat,AActor* Hero,ACineCameraActor* Camera,FString& Error)
{
 auto* A=NewObject<USceneDirectorAsset>(Outer);A->EventKey=Repeat?TEXT("석상_재상호작용"):TEXT("석상_첫상호작용");auto* Intro=StatueSource(Repeat?TEXT("Start_Skip"):TEXT("Start"));auto* Yes=StatueSource(TEXT("Choice_Yes"));auto* No=StatueSource(TEXT("Choice_No"));if(!Intro||!Yes||!No)return nullptr;
 // Source actors are attached to the checkpoint stage. Its shared translation is baked into editable path values.
 const FVector Origin=Hero->GetActorLocation()-FVector(0,200,196);
 auto Move=StatueMotion(Intro,false,Origin);auto Cam=StatueMotion(Intro,true,Origin);if(Move.MotionPoints.IsEmpty()||Cam.MotionPoints.IsEmpty()){Error=TEXT("원본 이동 트랙을 찾지 못했습니다.");return nullptr;}
 FDirectorActionEntry Heal;Heal.Key=TEXT("RestoreHP");Heal.ActionClass=USceneDirectorStatueRestoreAction::StaticClass();A->Actions.Add(Heal);
 for(auto* Path:{&Move,&Cam}){const double End=(Repeat?4.:139.)/30;if(Path->MotionPoints.Num()>1&&FMath::IsNearlyEqual(Path->MotionPoints[Path->MotionPoints.Num()-2].Time,End))Path->MotionPoints.Pop();else Path->MotionPoints.Last().Time=End;}
 FStatueGraph G{A};FDirectorStep Start;Start.Type=EDirectorNodeType::Start;const auto StartID=G.Add(Start);
 FDirectorStep Spawn;Spawn.Type=EDirectorNodeType::SpawnNPC;Spawn.Role=TEXT("Heroine");Spawn.ActorClass=Hero->GetClass();Spawn.Transform=Move.MotionPoints[0].Pose();Spawn.ImportedTemplate=DuplicateObject<AActor>(Hero,A);Spawn.ImportedTemplate->DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);Spawn.ImportedTemplate->SetActorHiddenInGame(false);const auto SpawnID=G.Add(Spawn);G.Link(StartID,SpawnID);
 FDirectorStep Mode;Mode.Type=EDirectorNodeType::CinematicMode;Mode.bHidePlayer=true;G.Setup=G.Add(Mode);G.Link(SpawnID,G.Setup);
 FDirectorCameraEntry C;C.Key=TEXT("StatueCamera");C.Transform=Cam.MotionPoints[0].Pose();C.ImportedTemplate=DuplicateObject<AActor>(Camera,A);C.ImportedTemplate->DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);auto* Lens=CastChecked<ACineCameraActor>(C.ImportedTemplate)->GetCineCameraComponent();Lens->SetCurrentFocalLength(20);Lens->SetCurrentAperture(2.8f);auto Focus=Lens->FocusSettings;Focus.ManualFocusDistance=100000;Lens->SetFocusSettings(Focus);C.FieldOfView=Lens->GetHorizontalFieldOfView();A->Cameras.Add(C);
 const auto IntroCam=G.At(G.Setup,0,Cam);const auto IntroMove=G.At(G.Setup,0,Move);
 FDirectorStep Visible;Visible.Type=EDirectorNodeType::Visibility;Visible.Role=TEXT("Heroine");Visible.bVisible=true;const auto Hide=G.At(G.Setup,0,Visible);Visible.bVisible=true;const auto Show=G.At(Hide,Repeat?0:135,Visible);
 // Dialogues pause the shared timeline while the source camera and character remain on the same frame.
 FGuid DialogueParent=G.Setup;int PreviousEnd=0;
 if(!Repeat)for(int N=1;N<=2;++N){const int Frame=120+N*5;DialogueParent=G.At(DialogueParent,Frame-PreviousEnd,StatueDialogue(N));PreviousEnd=Frame+1;}
 const int QuestionFrame=Repeat?0:135;DialogueParent=G.At(DialogueParent,QuestionFrame-PreviousEnd,StatueDialogue(3));
 FDirectorStep Choice=StatueDialogue(3);FDirectorChoice CY;CY.Key=TEXT("Rest");CY.Text=StatueText(4);FDirectorChoice CN;CN.Key=TEXT("Leave");CN.Text=StatueText(5);Choice.Choices={CY,CN};
 // The introductory clips end before selecting the continuation so all parallel work joins cleanly.
 FDirectorStep Join;Join.Type=EDirectorNodeType::Hub;const auto JoinID=G.Add(Join);for(auto ID:{IntroCam,IntroMove,Show,DialogueParent})G.Link(ID,JoinID);const auto ChoiceID=G.At(JoinID,0,Choice);
 FDirectorStep YHub;YHub.Type=EDirectorNodeType::Hub;auto Y=G.Add(YHub);FDirectorStep NHub;NHub.Type=EDirectorNodeType::Hub;auto N=G.Add(NHub);G.Get(ChoiceID).ChoiceTargets.Add(CY.Key,Y);G.Get(ChoiceID).ChoiceTargets.Add(CN.Key,N);
 FDirectorStep End;End.Type=EDirectorNodeType::End;G.End=G.Add(End);
 for(bool Rest:{true,false})
 {
 const auto Parent=Rest?Y:N;auto* Source=Rest?Yes:No;TArray<FGuid> Ends;Ends.Add(G.At(Parent,0,StatueMotion(Source,false,Origin)));Ends.Add(G.At(Parent,0,StatueMotion(Source,true,Origin)));
 if(Rest){StatueAnimations(G,Parent,Source,Ends);FDirectorStep Fade;Fade.Type=EDirectorNodeType::Fade;Fade.Duration=1;Fade.FadeFrom=0;Fade.FadeTo=1; // Separate ramp and hold retains the original 120..150 fade and 150..170 black interval.
 Fade.Duration=1;auto Ramp=G.At(Parent,120,Fade);Fade.FadeFrom=Fade.FadeTo=1;Fade.Duration=20.f/30;auto Hold=G.At(Ramp,0,Fade);Fade.FadeFrom=1;Fade.FadeTo=0;Fade.Duration=1;Ends.Add(G.At(Hold,0,Fade));Ends.Add(G.At(Parent,165,StatueDialogue(6)));FDirectorStep Recover;Recover.Type=EDirectorNodeType::GameAction;Recover.ActionKey=TEXT("RestoreHP");Ends.Add(G.At(Parent,165,Recover));}
 FDirectorStep Hidden=Visible;Hidden.bVisible=false;Ends.Add(G.At(Parent,Rest?199:4,Hidden));
 FDirectorStep Return;Return.Type=EDirectorNodeType::GameplayReturn;Return.Duration=1;auto ReturnID=G.Add(Return);for(auto ID:Ends)G.Link(ID,ReturnID);G.Link(ReturnID,G.End);
 }
 A->ImportedFrom=Intro;A->ImportReport=TEXT("석상 원본 4개 시퀀스의 카메라·이동·애니메이션·대사·선택지·페이드를 편집 가능한 노드로 재구성. 원본과 석상 BP 연결은 보존. 복구 선택 시 기존 Ac_Stats 체력 회복 함수를 호출. 원본에 실제 저장 함수는 없으므로 저장 기능은 추가하지 않음.");
 USceneDirectorLibrary::ArrangeDirectorGraph(A);
 if(!FSceneDirectorCompiler::Compile(*A,Error))return nullptr;return A;
}
}
USceneDirectorAsset* USceneDirectorLibrary::CreateStatuePerformance(UWorld* World,FString& Report)
{
 const FString Path=TEXT("/Game/SceneDirector/Statue/DA_StatueInteraction");if(FPackageName::DoesPackageExist(Path)){Report=TEXT("기존 결과를 덮어쓰지 않습니다.");return LoadObject<USceneDirectorAsset>(nullptr,*(Path+TEXT(".DA_StatueInteraction")));}
 AActor* Hero=nullptr;ACineCameraActor* Camera=nullptr;
 for(TActorIterator<AActor> It(World);It;++It){if(It->GetName()==TEXT("BP_NPC_Player_Heroine_11"))Hero=*It;if(It->GetName()==TEXT("CineCameraActor_15"))Camera=Cast<ACineCameraActor>(*It);}
 if(!Hero||!Camera){Report=TEXT("AbandonedSchool 원본 맵의 석상 캐릭터/카메라를 찾지 못했습니다.");return nullptr;}
 auto* Result=BuildStatue(GetTransientPackage(),false,Hero,Camera,Report);if(!Result)return nullptr;auto* Repeat=BuildStatue(Result,true,Hero,Camera,Report);if(!Repeat)return nullptr;Result->EventGraphs.Add(Repeat);
 auto* Asset=DuplicateObject<USceneDirectorAsset>(Result,CreatePackage(*Path),TEXT("DA_StatueInteraction"));Asset->SetFlags(RF_Public|RF_Standalone|RF_Transactional);FSavePackageArgs Args;Args.TopLevelFlags=RF_Public|RF_Standalone;Args.SaveFlags=SAVE_NoError;if(!UPackage::SavePackage(Asset->GetOutermost(),Asset,*FPackageName::LongPackageNameToFilename(Path,FPackageName::GetAssetPackageExtension()),Args)){Report=TEXT("저장 실패");return nullptr;}FAssetRegistryModule::AssetCreated(Asset);Report=Asset->ImportReport;return Asset;
}



void USceneDirectorLibrary::ArrangeDirectorGraph(USceneDirectorAsset* A)
{
 if(!A)return;A->Modify();
 TMap<FGuid,int32> Depth,Remaining;TMap<FGuid,TArray<FGuid>> Children;TArray<FGuid> Queue;
 for(const auto& S:A->Steps){Remaining.FindOrAdd(S.Id);Children.Add(S.Id,S.AllSuccessors());for(FGuid Next:S.AllSuccessors())++Remaining.FindOrAdd(Next);}
 for(const auto& S:A->Steps)if(Remaining[S.Id]==0)Queue.Add(S.Id);
 for(int I=0;I<Queue.Num();++I)for(FGuid Next:Children[Queue[I]]){Depth.FindOrAdd(Next)=FMath::Max(Depth.FindRef(Next),Depth.FindRef(Queue[I])+1);if(--Remaining[Next]==0)Queue.Add(Next);}
 TMap<int32,int32> Rows;for(auto& S:A->Steps){const int D=Depth.FindRef(S.Id);S.EditorPosition=FVector2D(D*340,Rows.FindOrAdd(D)++*220);}
 for(auto Event:A->EventGraphs)ArrangeDirectorGraph(Event);A->MarkPackageDirty();
}
