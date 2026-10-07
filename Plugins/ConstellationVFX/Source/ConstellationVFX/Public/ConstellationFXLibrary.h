#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "ConstellationFXLibrary.generated.h"
class AConstellationFXActor;
class UNiagaraSystem;
UENUM(BlueprintType)
enum class EConstellationFXKind : uint8 { SwordHit, SwordBlock, SwordParry, SlimeAttack, SlimeHit, RunDust, GlassBreak, CaveDust, CaveMist, WaterDrop, WaterRipple, CaveSpore, PlayerHit };
UCLASS()
class CONSTELLATIONVFX_API UConstellationFXLibrary : public UBlueprintFunctionLibrary {
 GENERATED_BODY()
public:
 static FLinearColor CombatColor(EConstellationFXKind Kind);
 static float CombatScale(EConstellationFXKind Kind);
 UFUNCTION(BlueprintCallable,Category="Constellation|Effects",meta=(WorldContext="WorldContext"))
 static AConstellationFXActor* SpawnEffect(const UObject* WorldContext,EConstellationFXKind Kind,FVector Location,FVector Direction,FLinearColor Color,float Scale=1.f);
 UFUNCTION(BlueprintCallable,Category="Constellation|Effects") static void StopEffectsForOwner(AActor* Owner);
 UFUNCTION(BlueprintCallable,Category="Constellation|Effects") static FString DescribeNiagara(UNiagaraSystem* System);
};
