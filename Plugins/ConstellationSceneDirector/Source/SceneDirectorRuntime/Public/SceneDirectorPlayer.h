#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorPerformance.h"
#include "SceneDirectorVision.h"
#include "SceneDirectorPlayer.generated.h"
class USceneDirectorAsset;
class ULevelSequencePlayer;
class ALevelSequenceActor;
class APlayerController;
class UAudioComponent;
class SWidget;
class FDirectorPerformance;
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FDirectorGameplayReturned);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FDirectorStopped,bool,bCompleted);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FDirectorChoiceSelected,FGuid,DialogueId,FName,ChoiceKey);
UCLASS(BlueprintType)
class SCENEDIRECTORRUNTIME_API ASceneDirectorPlayer : public AActor
{
    GENERATED_BODY()
public:
    ASceneDirectorPlayer();
    UFUNCTION(BlueprintPure,Category="시야 효과") bool HasEyeEffect() const;
    UFUNCTION(BlueprintPure,Category="시야 효과") bool HasStartedEyeEffect() const;
    UFUNCTION(BlueprintPure,Category="시야 효과") bool HasVisionOverlay() const {return VisionWidget.IsValid();}
    UFUNCTION(BlueprintPure,Category="시야 효과") float GetEyeOpen() const {return VisionState.EyeOpen;}
    UFUNCTION(BlueprintPure,Category="시야 효과") float GetVisionBlur() const {return VisionState.Blur;}
    UFUNCTION(BlueprintPure,Category="시야 효과") float GetVisionHaze() const {return VisionState.Haze;}

    UPROPERTY(BlueprintAssignable,Category="연출") FDirectorGameplayReturned OnGameplayReturned;
    bool CaptureGameplayPose(AActor* Target);
    // Gameplay deactivation must survive visual-track RestoreState until an explicit activation.
    void SetActorDeactivated(AActor* Target,bool bDeactivated);
    TOptional<FTransform> GameplayPose;
    UPROPERTY(BlueprintAssignable,Category="연출") FDirectorStopped OnDirectorStopped;
    UPROPERTY(EditInstanceOnly,BlueprintReadWrite,Category="기존 오브젝트",meta=(DisplayName="Key → 레벨 Actor")) TMap<FName,TObjectPtr<AActor>> ObjectBindings;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="기준 좌표",meta=(DisplayName="기준 좌표 사용")) bool bUseOrigin=false;
    UPROPERTY(EditInstanceOnly,BlueprintReadWrite,Category="기준 좌표",meta=(DisplayName="기준 Actor")) TObjectPtr<AActor> OriginActor;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="기준 좌표",meta=(DisplayName="기준 Transform")) FTransform OriginTransform;
    UFUNCTION(BlueprintCallable,Category="기존 오브젝트") AActor* ResolveObject(FName Key) const;

    UPROPERTY(EditDefaultsOnly,Category="대사 UI") TObjectPtr<class UTexture2D> DialogueBackground;
    UPROPERTY(EditDefaultsOnly,Category="대사 UI") TObjectPtr<class UTexture2D> DialogueContinue;
    UPROPERTY(EditDefaultsOnly,Category="대사 UI") TObjectPtr<class UTexture2D> DialogueSpeakerBackground;
    UPROPERTY() FDirectorChoiceStyle DialogueChoiceStyle;
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="선택지") TArray<FDirectorChoice> CurrentChoices;
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="선택지") FName LastChoiceKey;
    UPROPERTY(BlueprintAssignable,Category="선택지") FDirectorChoiceSelected OnChoiceSelected;
    UFUNCTION(BlueprintCallable,Category="선택지") bool SelectDialogueChoice(FName Key);
    UFUNCTION(BlueprintPure,Category="선택지") bool IsWaitingForChoice()const{return WaitingCue!=INDEX_NONE&&!CurrentChoices.IsEmpty();}
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="조건 변수",meta=(DisplayName="재생 초기값 덮어쓰기")) TMap<FName,bool> InitialBoolOverrides;
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="조건 변수") TMap<FName,bool> BoolValues;
    TMap<FName,int32> InitialIntOverrides,IntValues;
    EDirectorDialoguePosition CurrentDialoguePosition=EDirectorDialoguePosition::Bottom;
    bool bKeepCurrentDialogue=true;
    bool bReturningToGameplay=false;
    TMap<TWeakObjectPtr<AActor>,bool> StandInVisibility;
    TMap<TWeakObjectPtr<class UPrimitiveComponent>,bool> StandInComponentVisibility;
    void RememberStandIns();
    void RestoreStandIns();

    UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="게임 액션") TArray<FDirectorActionResult> ActionResults;
    FGuid ChoicePrompt;
    virtual ~ASceneDirectorPlayer() override;
    virtual void Tick(float DeltaSeconds) override;
    UFUNCTION(BlueprintCallable,Category="대사") void AdvanceDialogue();
    UFUNCTION(BlueprintPure,Category="대사") bool IsWaitingForDialogue() const {return WaitingCue!=INDEX_NONE;}
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="대사") FText CurrentSpeaker;
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="대사") FText CurrentDialogue;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="연출",meta=(DisplayName="연출 그래프")) TObjectPtr<USceneDirectorAsset> Director;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="연출",meta=(DisplayName="이벤트 그래프",GetOptions="GetEventOptions")) FName EventKey;
    UFUNCTION() TArray<FString> GetEventOptions() const;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="연출",meta=(DisplayName="게임 시작 시 재생")) bool bAutoPlay=true;
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="연출") FString LastError;
    UFUNCTION(BlueprintCallable,Category="연출") bool PlayDirector();
    UFUNCTION(BlueprintCallable,Category="연출") void StopDirector();
    UFUNCTION(BlueprintPure,Category="연출") bool IsDirectorPlaying() const {return SequencePlayer!=nullptr;}
UFUNCTION(BlueprintPure,Category="연출",meta=(DisplayName="String Key로 NPC 찾기")) AActor* FindNPC(FName Key) const;
UFUNCTION(BlueprintPure,Category="연출",meta=(DisplayName="String Key로 카메라 찾기")) AActor* FindCamera(FName Key) const;
protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
private:
    UPROPERTY(Transient) TWeakObjectPtr<AActor> HiddenPlayer;
    bool bPlayerWasHidden=false;
    UPROPERTY(Transient) TObjectPtr<USceneDirectorAsset> RuntimeSource;
    FTransform OriginDelta;
    bool bNaturalFinish=false;
    TSet<TWeakObjectPtr<AActor>> DeactivatedActors;
    void ApplyActorDeactivations();
    struct FControlledCharacter
    {
        uint8 MovementMode=0,CustomMode=0;
        FVector Velocity=FVector::ZeroVector;
        TMap<TWeakObjectPtr<class UPrimitiveComponent>,ECollisionEnabled::Type> Collisions;
        bool bStandIn=false;
    };
    TMap<TWeakObjectPtr<class ACharacter>,FControlledCharacter> ControlledCharacters;
    void ControlCharacters();
    void RestoreCharacter(class ACharacter* Character,const FControlledCharacter& State,bool bKeepInactive);
    void RestoreCharacters();
    void ApplyOrigin();
    bool bExecutingAction=false;
    UPROPERTY(Transient) TMap<FName,TSubclassOf<USceneDirectorAction>> ActiveActions;
    bool ExecuteGameAction(const FDirectorStep& Step);
    UPROPERTY(Transient) TObjectPtr<USceneDirectorAsset> BranchSource;
    UPROPERTY(Transient) TObjectPtr<USceneDirectorAsset> BranchPrefix;
    UPROPERTY(Transient) TMap<FName,TObjectPtr<AActor>> SessionNPCs;
    UPROPERTY(Transient) TMap<FName,TObjectPtr<AActor>> SessionCameras;
    UPROPERTY(Transient) TArray<TObjectPtr<AActor>> SessionOwnedActors;
    TMap<FGuid,FName> BranchDecisions;
    TMap<FName,bool> BranchInitialOverrides;
    FGuid PendingBranchChoice;
    bool bRebuildBranch=false;
    double BranchResumeSeconds=0;
    bool CompileBranchPrefix();
    bool RebuildBranchPlayback();
    bool PrepareBranchActors(double Frame);
    void BindBranchActors();
    UPROPERTY(Transient) TMap<FName,FGuid> ActiveNPCBindings;
    UPROPERTY(Transient) TMap<FName,FGuid> ActiveCameraBindings;
    UPROPERTY(Transient) TObjectPtr<ULevelSequencePlayer> SequencePlayer;
    UPROPERTY(Transient) TObjectPtr<ALevelSequenceActor> SequenceActor;
    UPROPERTY(Transient) TWeakObjectPtr<APlayerController> Controller;
    UPROPERTY(Transient) TWeakObjectPtr<AActor> OriginalViewTarget;
    FRotator OriginalControlRotation=FRotator::ZeroRotator;
    UPROPERTY(Transient) TArray<FDirectorCue> ActiveCues;
    UPROPERTY(Transient) TObjectPtr<UAudioComponent> VoiceComponent;
    UPROPERTY(Transient) TArray<TObjectPtr<AActor>> BoundActors;
    TArray<FTransform> OriginalTransforms;
    TUniquePtr<FDirectorPerformance> Performance;
    TSharedPtr<SWidget> VisionWidget;
    FDirectorVisionState VisionState;
    TSharedPtr<SWidget> DialogueWidget;
    TSharedPtr<class SDirectorDialogue> DialogueView;
    uint64 ChoiceInputFrame=MAX_uint64;
    TSet<int32> AdvancedCues, FiredControls;
    double ClockSeconds=0;
    int32 WaitingCue=INDEX_NONE, DialogueCue=INDEX_NONE;
    bool bManualClock=false,bInputLocked=false,bHUDHidden=false,bOriginalHUD=true,bOriginalCursor=false,bHasCursorSnapshot=false;
    void EvaluateConversation(double Seconds);
    void RestoreControls();
    void SetPlayerHidden(bool Hidden);
    void SetInputLocked(bool Locked);
    void SetHUDHidden(bool Hidden);
    bool bPlayerHandedBack=false;
    void HideGameWidgets();
    bool bHideGameWidgets=false;
    TMap<TWeakObjectPtr<class UUserWidget>,uint8> WidgetVisibility;

    UFUNCTION() void OnFinished();
};
