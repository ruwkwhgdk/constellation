#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "CombatEncounterDirector.generated.h"
class ACombatLabCharacter;
class UCombatAbilitySystem;
UENUM(BlueprintType)
enum class ECombatEncounterOutcome : uint8 { Active, Completed, Failed };
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FCombatEncounterOutcomeChanged,ECombatEncounterOutcome,Outcome);
UCLASS(BlueprintType)
class COMBATRUNTIME_API ACombatEncounterDirector : public AActor
{
 GENERATED_BODY()
public:
 ACombatEncounterDirector();
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Combat") int32 MaxAttackers=1;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Combat|Integration") FName BattleZoneKey;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Combat|Integration") bool bNotifySceneEvents=false;
 UPROPERTY(BlueprintReadOnly,Transient,Category="Combat|Integration") FGuid BattleInstance;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Combat") TArray<TObjectPtr<ACombatLabCharacter>> Enemies;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Combat") TObjectPtr<ACombatLabCharacter> Player;
 UPROPERTY(BlueprintReadOnly,Category="Combat") ECombatEncounterOutcome Outcome=ECombatEncounterOutcome::Active;
 UPROPERTY(BlueprintAssignable,Category="Combat") FCombatEncounterOutcomeChanged OnOutcomeChanged;
 bool CanAcquire(const UCombatAbilitySystem* System) const;
 bool Acquire(UCombatAbilitySystem* System);
 void Release(UCombatAbilitySystem* System);
 int32 ActiveAttackers() const;
 int32 LivingEnemies() const;
 virtual void Tick(float Delta) override;
private:
 TSet<TWeakObjectPtr<UCombatAbilitySystem>> Holders;
};
