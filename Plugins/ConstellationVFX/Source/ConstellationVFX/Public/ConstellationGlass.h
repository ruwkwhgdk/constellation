#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "ConstellationGlass.generated.h"
class UStaticMeshComponent;
class ASceneDirectorPlayer;
UCLASS(Blueprintable)
class CONSTELLATIONVFX_API AConstellationGlass : public AActor {
 GENERATED_BODY()
public:
 AConstellationGlass();
 virtual void OnConstruction(const FTransform& Transform) override;
 virtual float TakeDamage(float Damage,const FDamageEvent& Event,AController* Instigator,AActor* Causer) override;
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="Glass") TObjectPtr<UStaticMeshComponent> Pane;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Glass") FVector2D Size=FVector2D(120,180);
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Glass") FLinearColor Tint=FLinearColor(.6,.9,1,1);
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="Glass") bool bBroken=false;
 UFUNCTION(BlueprintCallable,Category="Glass") bool BreakGlass(FVector HitPoint,FVector Direction);
 UFUNCTION(BlueprintCallable,Category="Glass") void ResetGlass();
 bool BreakForScene(ASceneDirectorPlayer* Player);
 bool SetBrokenForScene(ASceneDirectorPlayer* Player,bool Broken);
 virtual void EndPlay(const EEndPlayReason::Type Reason) override;
 UFUNCTION() void OnSceneStopped(bool bCompleted);
private:
 TWeakObjectPtr<ASceneDirectorPlayer> SceneOwner;
 bool bBeforeSceneBroken=false;
};
