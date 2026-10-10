#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SchoolOpeningSceneActor.generated.h"
class ASceneDirectorPlayer;
class UStaticMeshComponent;
class UAudioComponent;
class USoundBase;
class SWidget;
class UUserWidget;
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
 UPROPERTY(EditAnywhere,Category="S0") TSubclassOf<UUserWidget> RegionTitleClass;
 UPROPERTY(VisibleInstanceOnly,BlueprintReadOnly,Transient,Category="S0") bool bCompleted=false;
 UPROPERTY(VisibleInstanceOnly,BlueprintReadOnly,Transient,Category="S0") bool bPending=true;
 UFUNCTION(BlueprintCallable,Category="S0") bool RunCue(ASceneDirectorPlayer* Player,FName Cue,float Seconds);
 UFUNCTION(BlueprintPure,Category="S0") bool IsGameplayInputAvailable() const;
 virtual void Tick(float DeltaSeconds) override;
protected:
 virtual void BeginPlay() override;
 virtual void EndPlay(const EEndPlayReason::Type Reason) override;
private:
 UFUNCTION() void DirectorStopped(bool Completed);
 void RemoveMask();
 void StopSound();
 UPROPERTY(Transient) TObjectPtr<UAudioComponent> Song;
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
};
