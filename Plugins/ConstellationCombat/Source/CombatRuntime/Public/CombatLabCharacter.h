#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "AbilitySystemInterface.h"
#include "InputActionValue.h"
#include "CombatLabCharacter.generated.h"
class SCombatWorkbench;
class ACombatEncounterDirector;
class UCombatAbilitySystem;
class UCombatVFXComponent;
class UCombatHitReactionComponent;
class UStaticMeshComponent;
class UCombatActionDefinition;
class UCombatAttackInput;
class UCombatPatternProfile;
class UCombatEnemyAgent;
class UCombatEncounterProfile;
class USpringArmComponent;
class UCameraComponent;
class UAnimSequence;
class UInputAction;
class UInputMappingContext;
class UEnhancedInputLocalPlayerSubsystem;
UCLASS()
class COMBATRUNTIME_API ACombatLabCharacter : public ACharacter, public IAbilitySystemInterface
{
    GENERATED_BODY()
public:
    ACombatLabCharacter();
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="Combat|AI") TObjectPtr<UCombatEnemyAgent> EnemyAgent;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Combat|AI") TObjectPtr<UCombatEncounterProfile> EncounterProfile;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Combat|Encounter") TObjectPtr<ACombatEncounterDirector> EncounterDirector;
    virtual UAbilitySystemComponent* GetAbilitySystemComponent() const override;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Combat") TObjectPtr<UCombatAbilitySystem> Combat;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Combat|VFX") TObjectPtr<UCombatVFXComponent> CombatVFX;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Combat|Hit Reaction") TObjectPtr<UCombatHitReactionComponent> HitReaction;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Combat|VFX") TObjectPtr<UStaticMeshComponent> Sword;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Combat") TObjectPtr<UCombatActionDefinition> Action;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Combat|Loadout") TObjectPtr<UCombatActionDefinition> SkillAction;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Combat|Loadout") TObjectPtr<UCombatActionDefinition> UltimateAction;
    UFUNCTION(BlueprintCallable, Category="Combat|Loadout") bool UseSpecialAction(bool Ultimate);
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Combat") TObjectPtr<UCombatAttackInput> AttackInput;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Combat") bool bTrainingEnemy = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Combat|AI") TObjectPtr<UCombatPatternProfile> PatternProfile;
    UPROPERTY(VisibleAnywhere) TObjectPtr<USpringArmComponent> Arm;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UCameraComponent> Camera;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Locomotion") TObjectPtr<UAnimSequence> IdleAnimation;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Locomotion") TObjectPtr<UAnimSequence> MoveAnimation;
    UPROPERTY(EditAnywhere, Category="Locomotion", meta=(ClampMin="1")) float AnimationMoveSpeed = 168.f;
    UFUNCTION(BlueprintCallable, Category="Combat") void ToggleTargetLock();
    UFUNCTION(BlueprintPure, Category="Combat") ACombatLabCharacter* GetLockedTarget() const { return LockedTarget.Get(); }

    UPROPERTY(EditAnywhere, Category="Project Controls") TObjectPtr<UInputAction> ProjectLookAction;
    UPROPERTY(EditAnywhere, Category="Project Controls") TObjectPtr<UInputMappingContext> ProjectInputContext;
    UPROPERTY(EditAnywhere, Category="Project Controls") float ProjectYawScale = 2.5f;
    UPROPERTY(EditAnywhere, Category="Project Controls") float ProjectPitchScale = -2.5f;
    UPROPERTY(EditAnywhere, Category="Project Controls") float ProjectPitchMin = -89.9f;
    UPROPERTY(EditAnywhere, Category="Project Controls") float ProjectPitchMax = 89.9f;
    bool bWorkbenchOpen = false;
    void ToggleWorkbench();
    void ClearWorkbench();
    void EnsureWorkbench();
    void ApplyProjectLook(const FInputActionValue& Value);
    virtual void UnPossessed() override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void SetupPlayerInputComponent(UInputComponent* Input) override;
    virtual float TakeDamage(float Amount, const FDamageEvent& Event, AController* Instigator, AActor* Causer) override;
private:
    TSharedPtr<SCombatWorkbench> Workbench;
    TWeakObjectPtr<ACombatLabCharacter> LockedTarget;
    bool CanLockTarget(const ACombatLabCharacter* Target, float Range) const;
    void UpdateTargetLock(float Delta);
    void UpdateLocomotion();
    void SetupProjectControls(UInputComponent* Input);
    void ClearProjectControls();
    UPROPERTY() TObjectPtr<UInputMappingContext> ActiveLookContext;
    TWeakObjectPtr<UEnhancedInputLocalPlayerSubsystem> ControlsSubsystem;

    void Attack();
    void UseSkill();
    void UseUltimate();
    void Dodge();
    void Cancel();
    void ResetReview();
#if !UE_BUILD_SHIPPING
    void ConfigureAutomatedReview();
    void ConfigureSpecialReview();
    void ConfigureGroupReview();
    void ConfigureMovementReview();
    void ConfigureVFXReview();
    void ConfigureComboReview();
    void ConfigureStaminaReview();
    void ConfigureHitReview();
    void ConfigureDodgeReview();
    void ConfigurePatternReview();
    void ConfigureEncounterReview();
#endif
};
