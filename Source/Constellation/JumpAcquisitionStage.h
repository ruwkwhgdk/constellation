#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SceneDirectorAction.h"
#include "JumpAcquisitionStage.generated.h"
class ASceneDirectorPlayer;class ACharacter;class UStaticMeshComponent;class UInstancedStaticMeshComponent;class UPointLightComponent;class UMaterialInterface;
class UAnimMontage;
/** Graph-driven mechanisms for the jump star. Camera and timing are authored in SceneDirector. */
UCLASS()
class CONSTELLATION_API AJumpAcquisitionStage : public AActor
{
 GENERATED_BODY()
public:
 AJumpAcquisitionStage();
 UPROPERTY(EditInstanceOnly,Category="Jump acquisition") TObjectPtr<AActor> Star;
 UPROPERTY(EditAnywhere,Category="Jump acquisition") FTransform HeroineTransform;
 UPROPERTY(EditAnywhere,Category="Jump acquisition") TObjectPtr<UMaterialInterface> ParticleMaterial;
 UPROPERTY(EditAnywhere,Category="Jump acquisition|Animation") TMap<FName,TObjectPtr<UAnimMontage>> AnimationMontages;
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Transient,Category="Jump acquisition") TObjectPtr<UAnimMontage> ActiveMontage;
 UPROPERTY(EditAnywhere,Category="Jump acquisition|Lighting",meta=(ClampMin="0")) float ContactLightIntensity=90.f;
 UPROPERTY(EditAnywhere,Category="Jump acquisition|Lighting",meta=(ClampMin="0")) float AbsorptionLightIntensity=120.f;
 UPROPERTY(EditAnywhere,Category="Jump acquisition|Lighting",meta=(ClampMin="0")) float FaceFillIntensity=35.f;
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Transient,Category="Jump acquisition") FName Phase;
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Transient,Category="Jump acquisition") bool bCompleted=false;
 UFUNCTION(BlueprintCallable,Category="Jump acquisition") bool RunCue(ASceneDirectorPlayer* Player,FName Cue,float Seconds);
 virtual void Tick(float DeltaSeconds) override;
protected:
 virtual void EndPlay(const EEndPlayReason::Type Reason) override;
private:
 UFUNCTION() void Finished(bool Completed);
 void Restore(bool Cancelled);
 UActorComponent* Ability()const;
 UPROPERTY() TObjectPtr<UStaticMeshComponent> StarMesh;
 UPROPERTY() TObjectPtr<UInstancedStaticMeshComponent> Motes;
 UPROPERTY() TObjectPtr<UPointLightComponent> Light;
 UPROPERTY() TObjectPtr<UPointLightComponent> FaceFill;
 UPROPERTY(Transient) TMap<FName,TObjectPtr<UAnimMontage>> RuntimeMontages;
 TWeakObjectPtr<ASceneDirectorPlayer> Director;
 TWeakObjectPtr<ACharacter> Character;
 FTransform BeforeCharacter,BeforeStar;
 FVector StarCenter,ContactPosition;
 float Elapsed=0,Duration=1;
 uint8 OldMovement=0,OldCustom=0;
 bool bOldStarHidden=false,bOldCollision=true,bOldPostDisabled=false,bAnimationInstalled=false,bCommitRequested=false;
};
UCLASS()
class CONSTELLATION_API UJumpAcquisitionAction : public USceneDirectorAction
{
 GENERATED_BODY()
public:
 virtual bool Execute_Implementation(ASceneDirectorPlayer* Player,AActor* Target,const FDirectorActionParameters& Parameters,FString& Error) override;
};
