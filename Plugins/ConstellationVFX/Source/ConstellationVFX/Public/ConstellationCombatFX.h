#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "ConstellationFXLibrary.h"
#include "ConstellationCombatFX.generated.h"
class UConstellationSwordRibbonComponent;

UENUM(BlueprintType)
enum class EConstellationAttackTrail : uint8 { Light1, Light2, Light3, Heavy1, Heavy2, LightParry, HeavyParry };
UENUM(BlueprintType)
enum class EConstellationContactResult : uint8 { Miss, Hit, Guard, PerfectGuard };

// Art candidates, not damage, timing, unlock or final balance settings.
USTRUCT(BlueprintType)
struct FConstellationTrailProfile
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere,BlueprintReadWrite) float Width=24.f;
    UPROPERTY(EditAnywhere,BlueprintReadWrite) float Lifetime=.18f;
    UPROPERTY(EditAnywhere,BlueprintReadWrite) float Brightness=1.7f;
    UPROPERTY(EditAnywhere,BlueprintReadWrite) FLinearColor Color=FLinearColor(.8f,.88f,1.f,1.f);
};

UCLASS()
class CONSTELLATIONVFX_API UConstellationCombatFX : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintPure,Category="Constellation|Combat FX") static FConstellationTrailProfile TrailProfile(EConstellationAttackTrail Kind);
    UFUNCTION(BlueprintCallable,Category="Constellation|Combat FX") static void ConfigureTrail(UConstellationSwordRibbonComponent* Ribbon,EConstellationAttackTrail Kind);
    // Call once with the authoritative contact result. Never call Hit as well as PerfectGuard.
    // TargetHitKind is selected by the receiver, independent of the attack's weight.
    UFUNCTION(BlueprintCallable,Category="Constellation|Combat FX",meta=(WorldContext="Context"))
    static AConstellationFXActor* SpawnContact(const UObject* Context,EConstellationContactResult Result,EConstellationFXKind TargetHitKind,FVector Position,FVector Direction);
};

// Both main-game and CombatRuntime adapters can drive this without a gameplay dependency.
// Owner death/reset: StopPresentation (no recovery pulse). Natural recovery: SetGroggy(false).
UCLASS(ClassGroup=Effects,meta=(BlueprintSpawnableComponent))
class CONSTELLATIONVFX_API UConstellationGroggyFXComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Effects") FVector LocalOffset=FVector(0,0,70);
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Effects",meta=(ClampMin="0.05",ClampMax="10")) float Scale=1.f;
    UFUNCTION(BlueprintCallable,Category="Effects") void SetGroggy(bool Active);
    UFUNCTION(BlueprintCallable,Category="Effects") void StopPresentation();
protected:
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
private:
    bool bGroggy=false;
    TWeakObjectPtr<AConstellationFXActor> Hold;
    TArray<TWeakObjectPtr<AConstellationFXActor>> Effects;
    AConstellationFXActor* Spawn(EConstellationFXKind Kind);
};
