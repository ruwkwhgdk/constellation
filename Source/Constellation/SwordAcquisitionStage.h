#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SceneDirectorAction.h"
#include "SwordAcquisitionStage.generated.h"
class ASceneDirectorPlayer; class ACharacter; class UUserWidget; class UItemAcquisitionDefinition;
class USwordAcquisitionAnimationSet; class UAnimMontage; class UStaticMeshComponent;
UCLASS()
class CONSTELLATION_API ASwordAcquisitionStage : public AActor
{
 GENERATED_BODY()
public:
 ASwordAcquisitionStage();
 UPROPERTY(EditInstanceOnly,Category="Sword acquisition") TObjectPtr<AActor> Sword;
 UPROPERTY(EditAnywhere,Category="Sword acquisition") FTransform HeroineTransform;
 UPROPERTY(EditAnywhere,Category="Sword acquisition") TObjectPtr<UItemAcquisitionDefinition> ItemDefinition;
 UPROPERTY(EditAnywhere,Category="Sword acquisition") TObjectPtr<USwordAcquisitionAnimationSet> AnimationSet;
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Transient,Category="Sword acquisition") FName AnimationClip;
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Transient,Category="Sword acquisition") float AnimationTime=0;
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Transient,Category="Sword acquisition") TObjectPtr<UUserWidget> AttackToast;
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Transient,Category="Sword acquisition") bool bCompleted=false;
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Transient,Category="Sword acquisition") FName Phase;
 UFUNCTION(BlueprintCallable,Category="Sword acquisition") bool RunCue(ASceneDirectorPlayer* Player,FName Cue);
 UFUNCTION(BlueprintPure,Category="Sword acquisition") bool IsShowingItem()const{return ItemRequest.IsValid();}
 virtual void Tick(float DeltaSeconds)override;
protected:
 virtual void EndPlay(const EEndPlayReason::Type Reason)override;
private:
 UFUNCTION() void Finished(bool Completed);
 UActorComponent* Ability()const;
 bool CombatUnlocked()const;
 void CloseItem();
 void Restore(bool Cancelled);
 void ShowToast();
 bool BeginAnimation();
 bool QueueAnimation(FName Cue);
 bool PlayAnimation(FName Clip);
 void TickAnimation();
 void RestoreAnimation(bool Cancelled);
 UPROPERTY(Transient) TMap<FName,TObjectPtr<UAnimMontage>> RuntimeMontages;
 UPROPERTY(Transient) TObjectPtr<UAnimMontage> ActiveMontage;
 TWeakObjectPtr<UStaticMeshComponent> SwordMesh;
 FTransform BeforeSwordMesh;
 TArray<FName> AnimationQueue;
 FName LoopAfterQueue;
 bool bAnimationInstalled=false,bAnimationWaiting=false,bOldPostDisabled=false;
 uint8 OldSwordMobility=0;
 TWeakObjectPtr<ASceneDirectorPlayer> Director;
 TWeakObjectPtr<ACharacter> Character;
 FGuid ItemRequest;
 FTransform BeforeCharacter;
 uint8 OldMovement=0,OldCustom=0;
 bool bOldHidden=false,bOldCollision=true,bOldPawnInput=false,bItemConfirmed=false,bCommitted=false,bToastPending=false;
};
UCLASS()
class CONSTELLATION_API USwordAcquisitionAction : public USceneDirectorAction
{
 GENERATED_BODY()
public:
 virtual bool Execute_Implementation(ASceneDirectorPlayer* Player,AActor* Target,const FDirectorActionParameters& Parameters,FString& Error)override;
};
