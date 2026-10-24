#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SceneDirectorGaze.h"
#include "SchoolOpeningSceneActor.generated.h"
class ASceneDirectorPlayer;
class UStaticMeshComponent;
class UAudioComponent;
class USoundBase;
class SWidget;
class UUserWidget;
class UAnimMontage;
class ACharacter;
/** S0 scene mechanisms. Timing and story remain editable in the director graph. */
UCLASS(BlueprintType)
class CONSTELLATION_API ASchoolOpeningSceneActor : public AActor
{
 GENERATED_BODY()
public:
 ASchoolOpeningSceneActor();
 UPROPERTY(EditInstanceOnly,Category="S0") TObjectPtr<AActor> Locker;
 UPROPERTY(EditInstanceOnly,Category="S0") TObjectPtr<AActor> Girl;
 UPROPERTY(EditAnywhere,Category="S0") FName DoorComponentName=TEXT("Door");
 UPROPERTY(EditAnywhere,Category="S0") float DoorOpenAngle=-105.f;
 UPROPERTY(EditAnywhere,Category="S0") FTransform ExitTransform=FTransform(FRotator(0,180,0),FVector(2600,0,100));
 UPROPERTY(EditAnywhere,Category="S0") TObjectPtr<USoundBase> GirlSong;
 UPROPERTY(EditAnywhere,Category="S0") TObjectPtr<USoundBase> DoorSound;
 UPROPERTY(EditAnywhere,Category="S0") TObjectPtr<USoundBase> FallSound;
 UPROPERTY(EditAnywhere,Category="S0") TObjectPtr<USoundBase> GirlRunSound;
 UPROPERTY(EditAnywhere,Category="S0") FVector GirlLookTarget=FVector(3185,0,214);
 UPROPERTY(EditAnywhere,Category="S0") TSubclassOf<UUserWidget> RegionTitleClass;
 UPROPERTY(EditAnywhere,Category="S0|Locker") TObjectPtr<UAnimMontage> LockerMontage;
 UPROPERTY(EditAnywhere,Category="S0|Locker") bool bUseFirstPersonHeadMask=false;
 UPROPERTY(EditAnywhere,Category="S0|Locker") FTransform FallTransform=FTransform(FRotator(0,180,0),FVector(3060,0,90));
 /** The graph owns the prone wait; Recover is the only way to leave it. */
 UPROPERTY(VisibleInstanceOnly,BlueprintReadOnly,Transient,Category="S0|Locker") FName LockerPhase;
 UPROPERTY(VisibleInstanceOnly,BlueprintReadOnly,Transient,Category="S0") bool bCompleted=false;
 UPROPERTY(VisibleInstanceOnly,BlueprintReadOnly,Transient,Category="S0") bool bPending=true;
 UFUNCTION(BlueprintCallable,Category="S0") bool RunCue(ASceneDirectorPlayer* Player,FName Cue,float Seconds);
 UFUNCTION(BlueprintPure,Category="S0") bool IsGameplayInputAvailable() const;
 virtual void Tick(float DeltaSeconds) override;
protected:
 virtual void BeginPlay() override;
 virtual void EndPlay(const EEndPlayReason::Type Reason) override;
private:
 friend class FSchoolOpeningSkipTest;
 UFUNCTION() void DirectorStopped(bool Completed);
 void RemoveMask();
 void StopSound();
 void ShowMovementTutorial();
 bool StartLockerMotion();
 void StartGirlLook();
 void RestoreLockerMotion(bool Cancelled);
 TWeakObjectPtr<ACharacter> LockerCharacter;
 FTransform BeforeLockerTransform;
 uint8 BeforeMovementMode=0,BeforeCustomMode=0,BeforeRootMotionMode=0,BeforeAnimTick=0,BeforeCollision=0;
 float RecoveryElapsed=0,RecoveryDuration=0,SettleElapsed=0;
 float BeforeLockerBoundsScale=1.f;
 bool bLockerPosePending=false,bBeforeLockerMeshVisible=true;
 uint64 LockerPoseStartFrame=0;
 bool bLockerHeadHiddenByScene=false;
 UPROPERTY(Transient) TObjectPtr<UAudioComponent> Song;
 UPROPERTY(Transient) TObjectPtr<UAudioComponent> RunSound;
 UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> Door;
 UPROPERTY(Transient) TObjectPtr<UUserWidget> RegionTitle;
 TWeakObjectPtr<ASceneDirectorPlayer> Director;
 TSharedPtr<SWidget> EyeMask;
 FRotator DoorClosed;
 float EyeOpen=0,EyeFrom=0,EyeTo=0,EyeTime=0,EyeDuration=0;
 float DoorTime=0,DoorDuration=0;
 float BootstrapTime=0;
 bool bStarted=false;
 FTimerHandle TitleTimer;
 FTimerHandle MovementTutorialTimer;
 FDirectorGazeDriver GirlGaze;
 bool bGirlLooking=false;
 float GirlLookElapsed=0;
};
