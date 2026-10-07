#include "SceneDirectorPlayer.h"
#include "SceneDirectorBranching.h"
#include "SceneDirectorCompiler.h"
#include "SceneDirectorNodeTypes.h"
#include "LevelSequencePlayer.h"
#include "LevelSequenceActor.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Components/AudioComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "EngineUtils.h"
#include "Engine/World.h"

bool ASceneDirectorPlayer::CompileBranchPrefix()
{
    auto* Prefix=NewObject<USceneDirectorAsset>(this,NAME_None,RF_Transient);
    FGuid Pending;FString Error;
    if(!BranchSource||!DirectorBranching::Resolve(*BranchSource,BranchDecisions,BranchInitialOverrides,*Prefix,Pending,Error)
        ||!FSceneDirectorCompiler::Compile(*Prefix,Error))
    {LastError=Error.IsEmpty()?TEXT("분기 구간을 생성하지 못했습니다."):Error;return false;}
    BranchPrefix=Prefix;PendingBranchChoice=Pending;return true;
}
void ASceneDirectorPlayer::BindBranchActors()
{
    // Empty overrides suppress the sequence's own spawner until the scheduled cue creates the session actor.
    for(const auto& Pair:ActiveNPCBindings)
    {
        TArray<AActor*> Actors;if(auto* Actor=SessionNPCs.Find(Pair.Key);Actor&&IsValid(Actor->Get()))Actors.Add(Actor->Get());
        SequenceActor->SetBinding(UE::MovieScene::FRelativeObjectBindingID(Pair.Value),Actors,false);
    }
    for(const auto& Pair:ActiveCameraBindings)
    {
        TArray<AActor*> Actors;if(auto* Actor=SessionCameras.Find(Pair.Key);Actor&&IsValid(Actor->Get()))Actors.Add(Actor->Get());
        SequenceActor->SetBinding(UE::MovieScene::FRelativeObjectBindingID(Pair.Value),Actors,false);
    }
}
bool ASceneDirectorPlayer::PrepareBranchActors(double Frame)
{
    bool Changed=false;UWorld* World=GetWorld();
    for(const auto& Cue:ActiveCues)
    {
        if(Cue.StartFrame>Frame)continue;const auto& S=Cue.Step;
        if(DirectorNodes::IsNPC(S.Type))
        {
            if(auto* Existing=SessionNPCs.Find(S.Role))
            {if(!IsValid(Existing->Get())){LastError=TEXT("연출 중 NPC가 제거되었습니다: ")+S.Role.ToString();return false;}continue;}
            AActor* Actor=nullptr;
            if(S.Type==EDirectorNodeType::BindNPC)
            {
                if(S.ActorSource==EDirectorActorSource::Player){if(Controller.IsValid())Actor=Controller->GetPawn();}
                else if(S.ActorSource==EDirectorActorSource::Object)Actor=ResolveObject(S.ObjectKey);
                else for(TActorIterator<AActor> It(World);It;++It)if(It->ActorHasTag(S.ActorTag))
                {if(Actor){LastError=TEXT("Actor 태그가 중복됩니다: ")+S.ActorTag.ToString();return false;}Actor=*It;}
                if(!Actor||!Actor->IsA(S.ActorClass)){LastError=TEXT("기존 NPC 또는 BP가 일치하지 않습니다: ")+S.Role.ToString();return false;}
                if(BoundActors.Contains(Actor)){LastError=TEXT("같은 기존 NPC를 여러 Key에 연결할 수 없습니다.");return false;}
                BoundActors.Add(Actor);OriginalTransforms.Add(Actor->GetActorTransform());
            }
            else
            {
                FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
                Params.ObjectFlags|=RF_Transient;Params.OverrideLevel=GetLevel();
                Params.Template=S.ImportedTemplate;Actor=World->SpawnActor<AActor>(S.ActorClass,S.Transform*OriginDelta,Params);
                if(!Actor){LastError=TEXT("NPC 생성 실패: ")+S.Role.ToString();return false;}
                SessionOwnedActors.Add(Actor);
            }
            SessionNPCs.Add(S.Role,Actor);Changed=true;
        }
        if(DirectorNodes::IsCamera(S.Type))
        {
            const FName Key=S.EffectiveCameraKey();
            if(auto* Existing=SessionCameras.Find(Key))
            {if(!IsValid(Existing->Get())){LastError=TEXT("연출 카메라가 제거되었습니다: ")+Key.ToString();return false;}continue;}
            const auto* Entry=BranchPrefix->Cameras.FindByPredicate([Key](const FDirectorCameraEntry& C){return C.Key==Key;});
            if(Entry&&!Entry->ObjectKey.IsNone())
            {
                auto* Existing=Cast<ACameraActor>(ResolveObject(Entry->ObjectKey));if(!Existing){LastError=TEXT("기존 카메라 연결 실패");return false;}
                if(BoundActors.Contains(Existing)){LastError=TEXT("같은 실제 Actor를 여러 NPC/카메라 Key에 연결할 수 없습니다.");return false;}BoundActors.Add(Existing);OriginalTransforms.Add(Existing->GetActorTransform());SessionCameras.Add(Key,Existing);Changed=true;continue;
            }
            FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
            Params.ObjectFlags|=RF_Transient;Params.OverrideLevel=GetLevel();
            Params.Template=Entry?Entry->ImportedTemplate.Get():nullptr;
            auto* Camera=World->SpawnActor<ACameraActor>(Params.Template?Params.Template->GetClass():ACameraActor::StaticClass(),(Entry?Entry->Transform:S.Transform)*OriginDelta,Params);
            if(!Camera){LastError=TEXT("카메라 생성 실패: ")+Key.ToString();return false;}
            Camera->GetCameraComponent()->SetFieldOfView(Entry?Entry->FieldOfView:S.FieldOfView);
            SessionCameras.Add(Key,Camera);SessionOwnedActors.Add(Camera);Changed=true;
        }
    }
    if(Changed)BindBranchActors();return true;
}
bool ASceneDirectorPlayer::RebuildBranchPlayback()
{
    bRebuildBranch=false;
    TSet<FGuid> CompletedDialogues,CompletedControls;
    for(int32 I:AdvancedCues)if(ActiveCues.IsValidIndex(I))CompletedDialogues.Add(ActiveCues[I].Step.Id);
    for(int32 I:FiredControls)if(ActiveCues.IsValidIndex(I))CompletedControls.Add(ActiveCues[I].Step.Id);
    if(!CompileBranchPrefix())return false;
    TMap<AActor*,FTransform> CurrentPoses;
    for(const auto& Pair:SessionNPCs)if(IsValid(Pair.Value))CurrentPoses.Add(Pair.Value,Pair.Value->GetActorTransform());
    for(const auto& Pair:SessionCameras)if(IsValid(Pair.Value))CurrentPoses.Add(Pair.Value,Pair.Value->GetActorTransform());
    AActor* View=Controller.IsValid()?Controller->GetViewTarget():nullptr;
    const bool bDisableCuts=SequencePlayer->GetDisableCameraCuts();
    SequencePlayer->OnFinished.RemoveDynamic(this,&ASceneDirectorPlayer::OnFinished);
    SequencePlayer->Stop();SequencePlayer=nullptr;
    if(IsValid(SequenceActor))SequenceActor->Destroy();SequenceActor=nullptr;
    for(const auto& Pair:CurrentPoses)if(IsValid(Pair.Key))Pair.Key->SetActorTransform(Pair.Value);
    if(Controller.IsValid()&&IsValid(View))Controller->SetViewTarget(View);
    if(VoiceComponent){VoiceComponent->Stop();VoiceComponent->DestroyComponent();VoiceComponent=nullptr;}
    ActiveCues=BranchPrefix->Cues;ActiveNPCBindings=BranchPrefix->NPCBindings;ActiveCameraBindings=BranchPrefix->CameraBindings;
    AdvancedCues.Reset();FiredControls.Reset();
    for(int32 I=0;I<ActiveCues.Num();++I)
    {
        if(CompletedDialogues.Contains(ActiveCues[I].Step.Id))AdvancedCues.Add(I);
        if(CompletedControls.Contains(ActiveCues[I].Step.Id))FiredControls.Add(I);
    }
    WaitingCue=DialogueCue=INDEX_NONE;if(!bKeepCurrentDialogue)CurrentSpeaker=CurrentDialogue=FText::GetEmpty();CurrentChoices.Reset();
    FMovieSceneSequencePlaybackSettings Settings;Settings.FinishCompletionStateOverride=EMovieSceneCompletionModeOverride::ForceRestoreState;
    ALevelSequenceActor* Out=nullptr;
    SequencePlayer=ULevelSequencePlayer::CreateLevelSequencePlayer(GetWorld(),BranchPrefix->GeneratedSequence,Settings,Out);SequenceActor=Out;
    if(!SequencePlayer){LastError=TEXT("선택 경로의 시퀀스 재생기를 만들 수 없습니다.");return false;}
    ApplyOrigin();
    SequencePlayer->OnFinished.AddDynamic(this,&ASceneDirectorPlayer::OnFinished);
    BindBranchActors();ClockSeconds=BranchResumeSeconds;
    if(!PrepareBranchActors(ClockSeconds*30))return false;
    SequencePlayer->SetDisableCameraCuts(bDisableCuts);SequencePlayer->Play();SequencePlayer->Pause();
    const double End=SequencePlayer->GetDuration().AsSeconds();
    SequencePlayer->SetPlaybackPosition(FMovieSceneSequencePlaybackParams(FFrameTime::FromDecimal(FMath::Min(ClockSeconds,End-.0001)*30.),EUpdatePositionMethod::Jump));
    EvaluateConversation(ClockSeconds);
    return SequencePlayer!=nullptr;
}
