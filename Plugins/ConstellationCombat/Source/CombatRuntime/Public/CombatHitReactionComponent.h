#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "CombatHitReactionComponent.generated.h"
class UCombatAbilitySystem;
class UAnimSequence;
class UAnimationAsset;
class USkeletalMeshComponent;
struct FCombatAcceptedDamage;

// Cosmetic presentation only. Damage acceptance and stun duration remain owned by combat.
UCLASS(ClassGroup=Combat, meta=(BlueprintSpawnableComponent))
class COMBATRUNTIME_API UCombatHitReactionComponent : public UActorComponent
{
 GENERATED_BODY()
public:
 UCombatHitReactionComponent();
 void Initialize(UCombatAbilitySystem* InCombat);
 void StopReaction();
 bool IsPresenting() const { return bPresenting; }
 UPROPERTY(EditAnywhere, Category="Combat|Hit Reaction") TSoftObjectPtr<UAnimSequence> FrontAnimation;
 UPROPERTY(EditAnywhere, Category="Combat|Hit Reaction") TSoftObjectPtr<UAnimSequence> BackAnimation;
 UPROPERTY(EditAnywhere, Category="Combat|Hit Reaction") TSoftObjectPtr<UAnimSequence> LeftAnimation;
 UPROPERTY(EditAnywhere, Category="Combat|Hit Reaction") TSoftObjectPtr<UAnimSequence> RightAnimation;
 virtual void TickComponent(float DeltaTime,ELevelTick TickType,FActorComponentTickFunction* ThisTickFunction) override;
protected:
 virtual void EndPlay(const EEndPlayReason::Type Reason) override;
private:
 void ReceiveHit(const FCombatAcceptedDamage& Hit);
 TWeakObjectPtr<UCombatAbilitySystem> Combat;
 TWeakObjectPtr<USkeletalMeshComponent> Mesh;
 UPROPERTY(Transient) TObjectPtr<UAnimationAsset> SavedAnimation;
 UPROPERTY(Transient) TArray<TObjectPtr<UAnimSequence>> LoadedClips;
 float SavedPosition=0, SavedRate=1, Elapsed=0, Duration=.35f;
 bool bSavedPlaying=false, bSavedLooping=false, bPresenting=false, bOwnsAnimation=false;
};
