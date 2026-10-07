#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Engine/EngineTypes.h"
#include "ConstellationFXLibrary.h"
#include "CombatVFXComponent.generated.h"
class UCombatAbilitySystem;
class UNiagaraComponent;
class UConstellationSwordRibbonComponent;
class UNiagaraSystem;
class USceneComponent;
class AConstellationFXActor;
struct FCombatConfirmedHit;

UENUM(BlueprintType)
enum class ECombatVFXStyle : uint8 { Auto, Sword, Slime };

UENUM(BlueprintType)
enum class ECombatVFXCueMode : uint8 { Default, Disabled, Builtin, Niagara };

USTRUCT(BlueprintType)
struct FCombatVFXCue
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Effect") ECombatVFXCueMode Mode=ECombatVFXCueMode::Default;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Effect",meta=(EditCondition="Mode == ECombatVFXCueMode::Builtin",EditConditionHides)) EConstellationFXKind Kind=EConstellationFXKind::SwordHit;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Effect",meta=(EditCondition="Mode == ECombatVFXCueMode::Niagara",EditConditionHides)) TObjectPtr<UNiagaraSystem> System;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Effect") FLinearColor Color=FLinearColor::White;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Effect",meta=(ClampMin="0.01",ClampMax="10")) float Scale=1.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Effect",meta=(ClampMin="0.05",ClampMax="10")) float Duration=2.f;
};

USTRUCT(BlueprintType)
struct FCombatFootSurfaceFX
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FLinearColor Color = FLinearColor(.34f,.25f,.17f,.45f);
    UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bSuppressDust = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) bool bWater = false;
};

// Optional presentation: never applies damage and only listens to accepted combat events.
UCLASS(ClassGroup=Combat, meta=(BlueprintSpawnableComponent))
class COMBATRUNTIME_API UCombatVFXComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UCombatVFXComponent();
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Combat|VFX") bool bPresentationEnabled = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Combat|VFX",meta=(DisplayName="공격 이펙트")) FCombatVFXCue AttackCue;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Combat|VFX",meta=(DisplayName="피격 이펙트")) FCombatVFXCue HitCue;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Combat|VFX") ECombatVFXStyle Style = ECombatVFXStyle::Auto;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Combat|VFX") FName WeaponComponentName = TEXT("Sword");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Combat|VFX") TSoftObjectPtr<UNiagaraSystem> SwordTrail;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Combat|VFX") FLinearColor SwordColor = FLinearColor(.8f,.88f,1.f,1.f);
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Combat|VFX") FLinearColor SlimeColor = FLinearColor(.32f,.12f,.5f,1.f);
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Combat|VFX|Feet", meta=(ClampMin="1")) float FootstepDistance = 100.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Combat|VFX|Feet", meta=(ClampMin="0")) float MinimumDustSpeed = 120.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Combat|VFX|Feet") TMap<TEnumAsByte<EPhysicalSurface>,FCombatFootSurfaceFX> SurfaceEffects;
    UFUNCTION(BlueprintCallable, Category="Combat|VFX") void Initialize(UCombatAbilitySystem* System);
    UFUNCTION(BlueprintCallable, Category="Combat|VFX") void SetPresentationEnabled(bool Enabled);
    UFUNCTION(BlueprintCallable, Category="Combat|VFX") void StopPresentation();
    UFUNCTION(BlueprintPure, Category="Combat|VFX") bool HasAttackPresentation() const;
    ECombatVFXStyle ResolveStyle() const;
    int32 GetWeaponRibbonSegments() const;
    bool IsAuthoredTrailReady() const;
    virtual void TickComponent(float Delta, ELevelTick TickType, FActorComponentTickFunction* TickFunction) override;
protected:
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
private:
    TWeakObjectPtr<UCombatAbilitySystem> Combat;
    UPROPERTY(Transient) TArray<TObjectPtr<UObject>> PresentationAssets;
    UPROPERTY(Transient) TObjectPtr<UNiagaraComponent> ActiveTrail;
    UPROPERTY(Transient) TObjectPtr<UConstellationSwordRibbonComponent> WeaponRibbon;
    FVector LastTipDirection=FVector::ZeroVector;
    float TipDirectionAge=0.f;
    FVector PreviousTip=FVector::ZeroVector;
    bool bPreviousTipValid=false;
    TArray<TWeakObjectPtr<AConstellationFXActor>> WarmupEffects;
    bool bRenderingWarmupDone=false;
    TWeakObjectPtr<AConstellationFXActor> SlimeAttack;
    TWeakObjectPtr<USceneComponent> Weapon;
    TSet<FName> OpenWindows;
    uint64 Execution = 0;
    float StepTravel = 0.f;
    bool bLeftFoot = false;
    void OpenWindow(uint64 Id,FName Window);
    void CloseWindow(uint64 Id,FName Window);
    void ConfirmedHit(const FCombatConfirmedHit& Hit);
    void StopAttackPresentation();
    void UpdateFeet(float Delta);
    bool SpawnCue(const FCombatVFXCue& Cue,const FVector& Position,const FVector& Direction,bool Attack);
    TArray<TWeakObjectPtr<UNiagaraComponent>> CueBursts;
    USceneComponent* ResolveWeapon();
    void PrepareReviewWeapon();
    void WarmupRendering();
    void UpdateWeaponRibbon(float Delta);
};
