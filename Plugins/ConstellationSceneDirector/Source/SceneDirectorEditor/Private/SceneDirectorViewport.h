#pragma once
#include "SceneDirectorNodeTypes.h"
#include "SEditorViewport.h"
#include "SDirectorDialogue.h"
#include "SDirectorVision.h"
#include "SceneDirectorPlayer.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorPerformance.h"
#include "Components/AudioComponent.h"
#include "Components/MeshComponent.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/SOverlay.h"
#include "Styling/CoreStyle.h"
#include "EditorViewportClient.h"
#include "ISequencer.h"
#include "Camera/CameraComponent.h"
#include "Camera/CameraActor.h"
#include "MovieSceneSequence.h"
#include "MovieScene.h"
#include "Tracks/MovieSceneCameraCutTrack.h"
#include "Tracks/MovieSceneSubTrack.h"
#include "Sections/MovieSceneSubSection.h"
#include "Sections/MovieSceneCameraCutSection.h"

class FDirectorViewportClient : public FEditorViewportClient
{
public:
    FDirectorViewportClient(UWorld* InWorld,TWeakPtr<ISequencer> InSequencer,const FVector& Focus,USceneDirectorAsset* InAsset)
        : FEditorViewportClient(nullptr),World(InWorld),Sequencer(InSequencer),Asset(InAsset)
    {
        SetViewLocation(Focus+FVector(-400,150,180));SetViewRotation((Focus+FVector(0,0,80)-GetViewLocation()).Rotation());
        SetGameView(true);SetViewMode(VMI_Unlit);SetRealtime(true);EngineShowFlags.SetSelectionOutline(false);
    }
    virtual ~FDirectorViewportClient() override {for(const auto& Pair:HiddenLevelActors)if(Pair.Key.IsValid())Pair.Key->SetIsTemporarilyHiddenInEditor(Pair.Value);Performance.Reset();if(Audio.IsValid()){Audio->Stop();Audio->DestroyComponent();}}
    struct FReturnPreview
    {
        FTransform View;float FOV=90;
        TMap<FName,FTransform> StandIns;
    };
    FTransform GameplayPreviewView;float GameplayPreviewFOV=90;
    TMap<FGuid,FReturnPreview> ReturnStarts;
    void CaptureReturnStart(const FGuid& Id)
    {
        FReturnPreview& Start=ReturnStarts.FindOrAdd(Id);Start.View=FTransform(GetViewRotation(),GetViewLocation());Start.FOV=ViewFOV;
        if(auto S=Sequencer.Pin())if(Asset.IsValid())for(const auto& Cue:Asset->Cues)if(Cue.Step.bPlayerStandIn)
            if(const auto* Binding=Asset->NPCBindings.Find(Cue.Step.Role))for(auto O:S->FindBoundObjects(*Binding,MovieSceneSequenceID::Root))
                if(auto* A=Cast<AActor>(O.Get()))Start.StandIns.Add(Cue.Step.Role,A->GetActorTransform());
    }
    FString PerformanceError;
    virtual UWorld* GetWorld() const override {return World.Get();}
    virtual void Tick(float DeltaSeconds) override
    {
        FEditorViewportClient::Tick(DeltaSeconds);
        if(auto S=Sequencer.Pin())
        {
            if(Asset.IsValid())
            {
                PerformanceError.Reset();
                UpdatePreviewCharacters(*S);
                Performance.Evaluate(Asset->Cues,S->GetGlobalTime().Time.AsDecimal(),[&](FName Key)->AActor*
                {
                    const FGuid* ID=Asset->NPCBindings.Find(Key);if(!ID)return nullptr;
                    for(auto O:S->FindBoundObjects(*ID,MovieSceneSequenceID::Root))if(auto* A=Cast<AActor>(O.Get()))return A;return nullptr;
                },PerformanceError);
                const double Frame=S->GetGlobalTime().Time.AsDecimal();int32 Speaking=INDEX_NONE;
                if(S->GetPlaybackStatus()==EMovieScenePlayerStatus::Playing)for(int32 I=0;I<Asset->Cues.Num();++I)
                {const auto& C=Asset->Cues[I];if(C.Step.Type==EDirectorNodeType::Dialogue&&C.Step.Voice&&Frame>=C.StartFrame&&Frame<C.EndFrame){Speaking=I;break;}}
                if(Speaking!=AudioCue||Frame<LastFrame)
                {
                    if(Audio.IsValid()){Audio->Stop();Audio->DestroyComponent();}Audio.Reset();AudioCue=Speaking;
                    if(Speaking!=INDEX_NONE){const auto& C=Asset->Cues[Speaking];Audio=UGameplayStatics::SpawnSound2D(World.Get(),C.Step.Voice,1,1,float((Frame-C.StartFrame)/30.),nullptr,false,false);}
                }
                LastFrame=Frame;
            }
            // Standalone asset editors have no level viewport camera cache. Resolve root and reused cuts directly.
            auto ApplyCuts=[&](UMovieScene* Movie,FMovieSceneSequenceID ID,FFrameTime Time)
            {
                if(auto* Cuts=Movie->GetCameraCutTrack())if(!Cuts->IsEvalDisabled())for(auto* Base:Cuts->GetAllSections())
                    if(auto* Cut=Cast<UMovieSceneCameraCutSection>(Base))if(Cut->IsActive()&&!Cuts->IsRowEvalDisabled(Cut->GetRowIndex())&&Cut->GetRange().Contains(Time.FrameNumber))
                        for(auto Object:S->FindBoundObjects(Cut->GetCameraBindingID().GetGuid(),ID))
                            if(auto* Actor=Cast<ACameraActor>(Object.Get()))
                            {
                                auto* Camera=Actor->GetCameraComponent();SetViewLocation(Camera->GetComponentLocation());SetViewRotation(Camera->GetComponentRotation());ViewFOV=Camera->FieldOfView;
                                const float Weight=Cut->EvaluateEasing(Time);
                                if(Weight<1)for(auto* Other:Cuts->GetAllSections())if(Other!=Cut&&Other->IsActive()&&!Cuts->IsRowEvalDisabled(Other->GetRowIndex())&&Other->HasEndFrame()&&Other->GetExclusiveEndFrame()==Cut->GetInclusiveStartFrame())
                                    if(auto* Prev=Cast<UMovieSceneCameraCutSection>(Other))for(auto O:S->FindBoundObjects(Prev->GetCameraBindingID().GetGuid(),ID))if(auto* P=Cast<ACameraActor>(O.Get()))
                                    {auto* PC=P->GetCameraComponent();SetViewLocation(FMath::Lerp(PC->GetComponentLocation(),Camera->GetComponentLocation(),Weight));SetViewRotation(FQuat::Slerp(PC->GetComponentQuat(),Camera->GetComponentQuat(),Weight).Rotator());ViewFOV=FMath::Lerp(PC->FieldOfView,Camera->FieldOfView,Weight);}
                            }
            };
            auto* Movie=S->GetRootMovieSceneSequence()->GetMovieScene();const FFrameTime Time=S->GetGlobalTime().Time;
            ApplyCuts(Movie,MovieSceneSequenceID::Root,Time);
            for(auto* Track:Movie->GetTracks())if(auto* SubTrack=Cast<UMovieSceneSubTrack>(Track))if(!SubTrack->IsEvalDisabled())
                for(auto* Base:SubTrack->GetAllSections())if(auto* Sub=Cast<UMovieSceneSubSection>(Base))
                    if(Sub->IsActive()&&!SubTrack->IsRowEvalDisabled(Sub->GetRowIndex())&&Sub->GetRange().Contains(Time.FrameNumber)&&Sub->GetSequence())
                        ApplyCuts(Sub->GetSequence()->GetMovieScene(),Sub->GetSequenceID(),Time*Sub->OuterToInnerTransform());
        }
        if(auto S=Sequencer.Pin())ApplyGameplayReturn(*S);
        Invalidate();
    }
private:
    void ApplyGameplayReturn(ISequencer& S)
    {
        if(!Asset.IsValid())return;
        const double Frame=S.GetGlobalTime().Time.AsDecimal();const FDirectorCue* Latest=nullptr;
        for(const auto& C:Asset->Cues)if(C.StartFrame<=Frame&&(DirectorNodes::IsReturn(C.Step.Type)||C.Step.Type==EDirectorNodeType::CinematicMode||(DirectorNodes::IsCamera(C.Step.Type)&&((C.Step.Type!=EDirectorNodeType::CameraMove&&C.Step.Type!=EDirectorNodeType::CameraPreset)||C.Step.bActivateCamera))||(C.Step.Type==EDirectorNodeType::Sequence&&DirectorSequence::HasCamera(C.Step))))
            if(!Latest||C.StartFrame>=Latest->StartFrame)Latest=&C;
        if(!Latest||!DirectorNodes::IsReturn(Latest->Step.Type))return;
        const auto* Start=ReturnStarts.Find(Latest->Step.Id);if(!Start)return;
        const auto& Step=Latest->Step;const FTransform Goal=Step.bUsePreviewReturnView?Step.PreviewReturnView:GameplayPreviewView;
        const float Alpha=FMath::Clamp(float((Frame-Latest->StartFrame)/FMath::Max(1,Latest->EndFrame-Latest->StartFrame)),0.f,1.f);
        SetViewLocation(FMath::Lerp(Start->View.GetLocation(),Goal.GetLocation(),Alpha));
        SetViewRotation(FQuat::Slerp(Start->View.GetRotation(),Goal.GetRotation(),Alpha).Rotator());
        ViewFOV=FMath::Lerp(Start->FOV,Step.bUsePreviewReturnView?Step.PreviewReturnFOV:GameplayPreviewFOV,Alpha);
        // There is no live player pawn in an editor preview. Keep its cinematic stand-in at the handoff pose.
        for(const auto& Pose:Start->StandIns)if(const auto* Binding=Asset->NPCBindings.Find(Pose.Key))
            for(auto O:S.FindBoundObjects(*Binding,MovieSceneSequenceID::Root))if(auto* A=Cast<AActor>(O.Get()))
            {A->SetActorTransform(Pose.Value);A->SetActorHiddenInGame(false);}
    }
    // Preview spawnables replace their level counterparts only for the lifetime of this viewport.
    TMap<TWeakObjectPtr<AActor>,bool> HiddenLevelActors;
    TSet<TWeakObjectPtr<AActor>> InitializedNPCs;
    void UpdatePreviewCharacters(ISequencer& S)
    {
        const double Frame=S.GetGlobalTime().Time.AsDecimal();
        bool Returning=false;
        for(const auto& Cue:Asset->Cues)if(Cue.StartFrame<=Frame)
        {
            if(DirectorNodes::IsReturn(Cue.Step.Type))Returning=true;
            else if(Cue.Step.Type==EDirectorNodeType::CinematicMode)Returning=false;
        }
        for(const auto& Cue:Asset->Cues)
        {
            const auto& Step=Cue.Step;if(Step.Type!=EDirectorNodeType::BindNPC)continue;
            const FGuid* ID=Asset->NPCBindings.Find(Step.Role);if(!ID)continue;
            for(auto Object:S.FindBoundObjects(*ID,MovieSceneSequenceID::Root))if(auto* Preview=Cast<AActor>(Object.Get()))
            {
                if(!InitializedNPCs.Contains(Preview))
                {
                    InitializedNPCs.Add(Preview);
                    Preview->SetActorHiddenInGame(false);Preview->SetIsTemporarilyHiddenInEditor(false);
                    // Runtime ActivateNPC actions are deliberately not executed in the editor.
                    for(auto* Component:Preview->GetComponents())if(auto* Mesh=Cast<UMeshComponent>(Component)){Mesh->SetVisibility(true);Mesh->SetHiddenInGame(false);}
                    FName Tag=Step.ActorTag;
                    if(Step.ActorSource==EDirectorActorSource::Object)
                    {const auto* Entry=Asset->Objects.FindByPredicate([&](const FDirectorObjectEntry& E){return E.Key==Step.ObjectKey;});Tag=Entry?Entry->ActorTag:NAME_None;}
                    if(!Tag.IsNone()&&World.IsValid())for(TActorIterator<AActor> It(World.Get());It;++It)
                        if(*It!=Preview&&!It->HasAnyFlags(RF_Transient)&&It->ActorHasTag(Tag)&&It->IsA(Step.ActorClass))
                        {if(!HiddenLevelActors.Contains(*It))HiddenLevelActors.Add(*It,It->IsTemporarilyHiddenInEditor());It->SetIsTemporarilyHiddenInEditor(true);}
                }
                if(Step.bPlayerStandIn)Preview->SetActorHiddenInGame(Returning);
            }
        }
    }
    TWeakObjectPtr<UWorld> World;TWeakPtr<ISequencer> Sequencer;TWeakObjectPtr<USceneDirectorAsset> Asset;FDirectorPerformance Performance;TWeakObjectPtr<UAudioComponent> Audio;int32 AudioCue=INDEX_NONE;double LastFrame=-1;
};
class SDirectorViewport : public SEditorViewport
{
public:
    SLATE_BEGIN_ARGS(SDirectorViewport) {} SLATE_END_ARGS()
    void Construct(const FArguments&,UWorld* InWorld,TSharedPtr<ISequencer> InSequencer,FVector InFocus,USceneDirectorAsset* InAsset=nullptr)
    {World=InWorld;Sequencer=InSequencer;Focus=InFocus;Asset=InAsset;SEditorViewport::Construct(SEditorViewport::FArguments());}
protected:
    virtual void PopulateViewportOverlays(TSharedRef<SOverlay> Overlay) override
    {
        Overlay->AddSlot().VAlign(VAlign_Fill).HAlign(HAlign_Fill)
        [SNew(SDirectorVision).State_Lambda([this]{auto S=Sequencer.Pin();return S&&Asset.IsValid()?DirectorVision::Evaluate(Asset->Cues,S->GetGlobalTime().Time.AsDecimal()):FDirectorVisionState();})];
        const auto* Defaults=GetDefault<ASceneDirectorPlayer>();
        Overlay->AddSlot().VAlign(VAlign_Fill).HAlign(HAlign_Fill).Padding(12)
        [SNew(SDirectorDialogue).Position_Lambda([this]{const auto* C=GetDialogueCue();return C?C->Step.DialoguePosition:EDirectorDialoguePosition::Bottom;}).Background(Defaults->DialogueBackground).Continue(Defaults->DialogueContinue).SpeakerBackground(Defaults->DialogueSpeakerBackground)
         .ChoiceStyle(Defaults->DialogueChoiceStyle)
         .Choices_Lambda([this]{const auto* C=GetDialogueCue();return C?C->Step.Choices:TArray<FDirectorChoice>();})
         .ChoicePrompt_Lambda([this]{const auto* C=GetDialogueCue();return C?C->Step.Id:FGuid();})
         .Speaker_Lambda([this]{const auto* C=GetDialogueCue();return C?C->Step.ResolveSpeaker():FText::GetEmpty();})
         .Dialogue_Lambda([this]{const auto* C=GetDialogueCue();return C?C->Step.DialogueText:FText::GetEmpty();})
         .Waiting_Lambda([this]{const auto* C=GetDialogueCue();return C&&C->Step.DialogueAdvance==EDirectorDialogueAdvance::Click;})];
        Overlay->AddSlot().VAlign(VAlign_Top).Padding(10)
        [SNew(STextBlock).ColorAndOpacity(FLinearColor::Red).AutoWrapText(true).Text_Lambda([this]
         {return Client.IsValid()?FText::FromString(static_cast<FDirectorViewportClient*>(Client.Get())->PerformanceError):FText::GetEmpty();})];
    }
    const FDirectorCue* GetDialogueCue() const
    {
        auto S=Sequencer.Pin();if(!S||!Asset.IsValid())return nullptr;
        const double Frame=S->GetGlobalTime().Time.AsDecimal();
        const FDirectorCue* Latest=nullptr;
        for(const auto& C:Asset->Cues)if(C.StartFrame<=Frame){if((C.Step.Type==EDirectorNodeType::Dialogue||C.Step.Type==EDirectorNodeType::CloseDialogue||C.Step.Type==EDirectorNodeType::GameplayReturn)&&(!Latest||C.StartFrame>=Latest->StartFrame))Latest=&C;}
        return Latest&&Latest->Step.Type==EDirectorNodeType::Dialogue&&(Frame<Latest->EndFrame||Latest->Step.bKeepDialogueOpen)?Latest:nullptr;
    }

    virtual TSharedRef<FEditorViewportClient> MakeEditorViewportClient() override
    {return MakeShared<FDirectorViewportClient>(World.Get(),Sequencer,Focus,Asset.Get());}
private:
    TWeakObjectPtr<UWorld> World;TWeakPtr<ISequencer> Sequencer;FVector Focus;TWeakObjectPtr<USceneDirectorAsset> Asset;
};
