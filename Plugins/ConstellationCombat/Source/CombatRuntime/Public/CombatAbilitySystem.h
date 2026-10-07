#pragma once
#include "CoreMinimal.h"
#include "AbilitySystemComponent.h"
#include "CombatHitLedger.h"
#include "CombatObservation.h"
#include "CombatAbilitySystem.generated.h"
class UCombatAttributes;
class UCombatActionDefinition;
class UCombatActionAbility;

UENUM(BlueprintType)
enum class ECombatActionResult : uint8 { Succeeded, Cancelled, Failed };
DECLARE_MULTICAST_DELEGATE_TwoParams(FCombatActionEnded, uint64, ECombatActionResult);
DECLARE_MULTICAST_DELEGATE(FCombatDied);
DECLARE_MULTICAST_DELEGATE(FCombatHitReceived);
struct FCombatAcceptedDamage
{
    TWeakObjectPtr<AActor> Source;
    FVector LocalSourceDirection = FVector::ForwardVector;
    float AppliedDamage = 0.f;
};
DECLARE_MULTICAST_DELEGATE_OneParam(FCombatDamageAccepted, const FCombatAcceptedDamage&);

// Captured before damage callbacks can cancel or replace the source execution.
struct FCombatConfirmedHit
{
    uint64 ExecutionId = 0;
    FName Window;
    TWeakObjectPtr<AActor> Source;
    TWeakObjectPtr<AActor> Target;
    FVector Position = FVector::ZeroVector;
    FVector Normal = FVector::UpVector;
    float AppliedDamage = 0.f;
};
DECLARE_MULTICAST_DELEGATE_OneParam(FCombatHitConfirmed, const FCombatConfirmedHit&);
DECLARE_MULTICAST_DELEGATE_TwoParams(FCombatWindowChanged, uint64, FName);

UCLASS(ClassGroup=Combat, meta=(BlueprintSpawnableComponent))
class COMBATRUNTIME_API UCombatAbilitySystem : public UAbilitySystemComponent
{
    GENERATED_BODY()
public:
    UCombatAbilitySystem();
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;
    virtual bool GetShouldTick() const override;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Combat|Stamina", meta=(ClampMin="0")) float StaminaRecoveryPerSecond = 20.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Combat|Stamina", meta=(ClampMin="0", Units="s")) float StaminaRecoveryDelay = 1.f;
    // Resource defaults are applied once by InitializeCombat.
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Combat|Resources", meta=(ClampMin="0.01")) float MaxHealth = 100.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Combat|Resources", meta=(ClampMin="0.01")) float MaxStamina = 100.f;
    UFUNCTION(BlueprintPure, Category="Combat") float GetMaxHealth() const;
    UFUNCTION(BlueprintPure, Category="Combat") float GetMaxStamina() const;
    UFUNCTION(BlueprintPure, Category="Combat") float GetUltimateCharge() const;
    void InitializeCombat(AActor* Actor);
    void ResetAfterReturn();
    UFUNCTION(BlueprintCallable, Category="Combat") bool TryStartAction(UCombatActionDefinition* Action);
    UFUNCTION(BlueprintCallable, Category="Combat") void CancelAction();
    UFUNCTION(BlueprintPure, Category="Combat") bool IsActing() const { return ActiveAbility != nullptr; }
    UFUNCTION(BlueprintPure, Category="Combat") float GetHealth() const;
    UFUNCTION(BlueprintPure, Category="Combat") float GetStamina() const;
    UFUNCTION(BlueprintCallable, Category="Combat") bool ReceiveCombatDamage(float Damage, AActor* Source);
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Combat") int32 TeamId = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Combat") bool bDrawHitDebug = true;
    UPROPERTY(BlueprintReadOnly, Category="Combat") FString LastReason;
    UPROPERTY(BlueprintReadOnly,Category="Combat|AI") FString LastPatternDecision;
    UPROPERTY(BlueprintReadOnly,Category="Combat|AI") FName LastSelectedPattern;
    FCombatActionEnded OnActionEnded;
    FCombatDied OnDied;
    FCombatHitReceived OnHitReceived;
    FCombatDamageAccepted OnDamageAccepted;
    FCombatHitReceived OnPresentationReset;
    FCombatHitConfirmed OnHitConfirmed;
    FCombatWindowChanged OnHitWindowOpened;
    FCombatWindowChanged OnHitWindowClosed;
    FCombatHitReceived OnDodgeStarted;
    UFUNCTION(BlueprintCallable, Category="Combat") bool TryDodge(FVector Direction);
    UFUNCTION(BlueprintCallable, Category="Combat") void CancelDodge();
    UFUNCTION(BlueprintPure, Category="Combat") bool IsDodging() const { return bDodging; }
    UFUNCTION(BlueprintPure, Category="Combat") bool IsInvulnerable() const;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Combat|Dodge", meta=(ClampMin="0.01", Units="s")) float DodgeDuration=.6f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Combat|Dodge", meta=(ClampMin="0", Units="cm")) float DodgeDistance=240.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Combat|Dodge", meta=(ClampMin="0")) float DodgeStaminaCost=20.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Combat|Dodge", meta=(ClampMin="0", Units="s")) float DodgeInvulnerableStart=.1f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Combat|Dodge", meta=(ClampMin="0", Units="s")) float DodgeInvulnerableEnd=.3f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Combat|Hit Reaction", meta=(ClampMin="0", Units="s")) float HitReactionDuration = .35f;
    UFUNCTION(BlueprintPure, Category="Combat") bool IsHitReacting() const { return HitReactionRemaining > 0.f; }
    UFUNCTION(BlueprintPure, Category="Combat") float GetHitReactionRemaining() const { return HitReactionRemaining; }

    bool IsDodgeCancelWindowOpen() const;
    FCombatActionObservation ObserveAction() const;
    float GetCooldownRemaining(const UCombatActionDefinition* Action) const;
    const TArray<FCombatDamageRecord>& GetDamageHistory() const {return DamageHistory;}
    bool CanStart(const UCombatActionDefinition* Action, FString& Reason) const;
    bool AllowsExternalAction(FString& Reason) const;
    bool BeginExecution(UCombatActionAbility* Ability, UCombatActionDefinition* Action);
    bool CommitExecution();
    void CloseExecution();
    void FinishExecution(UCombatActionAbility* Ability, ECombatActionResult Result);
    bool MatchesMontageInstance(int32 InstanceId) const;
    void OpenHitWindow(FName Window, int32 InstanceId);
    void TickHitWindow(FName Window, int32 InstanceId);
    void CloseHitWindow(FName Window, int32 InstanceId);
    bool ApplyHit(FName Window, AActor* Target);
    bool ApplyHit(FName Window, AActor* Target, const FVector& Position, const FVector& Normal);
    uint64 GetExecutionId() const { return Ledger.GetExecution(); }
    UCombatActionDefinition* GetActiveAction() const { return ActiveAction; }
protected:
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
private:
    UPROPERTY() TObjectPtr<UCombatAttributes> Attributes;
    UPROPERTY() TObjectPtr<UCombatActionAbility> ActiveAbility;
    UPROPERTY() TObjectPtr<UCombatActionDefinition> ActiveAction;
    UPROPERTY() TMap<TObjectPtr<UCombatActionDefinition>, FGameplayAbilitySpecHandle> GrantedActions;
    TMap<TWeakObjectPtr<UCombatActionDefinition>, double> Cooldowns;
    FCombatHitLedger Ledger;
    TArray<FCombatDamageRecord> DamageHistory;
    void RecordDamage(float Damage,AActor* Source,bool Avoided);
    bool bDodging=false;
    bool bStartingDodge=false;
    uint16 DodgeMotionId=0;
    uint16 ActionMotionId=0;
    void StopActionMotion();
    uint64 DodgeSerial=0;
    float DodgeElapsed=0.f, ActiveDodgeDuration=0.f, ActiveInvulnerableStart=0.f, ActiveInvulnerableEnd=0.f;
    float HitReactionRemaining = 0.f;
    bool bResolvingDamage = false;
    float RecoveryDelayRemaining = 0.f;
    bool bInitialized = false;
    bool bDead = false;
    bool bCommitted = false;
    bool bCommittingResources=false;
    mutable bool bCheckingExternalGate=false;
    int32 MontageInstanceId = INDEX_NONE;
    void ModifyAttribute(const FGameplayAttribute& Attribute, float Delta, AActor* Source);
};
