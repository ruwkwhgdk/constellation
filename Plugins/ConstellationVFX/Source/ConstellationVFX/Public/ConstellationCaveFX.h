#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "ConstellationCaveFX.generated.h"
class ASceneDirectorPlayer;
UCLASS(Blueprintable)
class CONSTELLATIONVFX_API AConstellationCaveFX : public AActor {
 GENERATED_BODY()
public:
 AConstellationCaveFX();
 virtual void Tick(float Delta) override;
 virtual void EndPlay(const EEndPlayReason::Type Reason) override;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Cave") bool bEnabled=true;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Cave") bool bMist=true;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Cave") bool bSpores=false;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Cave") bool bDrips=true;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Cave",meta=(ClampMin="100")) float ActiveDistance=2200;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Cave",meta=(ClampMin="20")) float Radius=250;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Cave",meta=(ClampMin="20")) float CeilingHeight=220;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Cave") FLinearColor MistColor=FLinearColor(.17,.25,.3,.13);
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Cave") FLinearColor SporeColor=FLinearColor(.2,.8,.7,.55);
 UFUNCTION(BlueprintCallable,Category="Cave") void SetEffectsEnabled(bool Enabled);
 bool ApplySceneEnabled(ASceneDirectorPlayer* Player,bool Enabled);
 UFUNCTION() void OnSceneStopped(bool bCompleted);
private:
 TWeakObjectPtr<ASceneDirectorPlayer> SceneOwner; bool bBeforeScene=true;
 float DustClock=0,MistClock=0,DropClock=0,SporeClock=0;
 struct FDrop {float Time;FVector Point;};TArray<FDrop> Drops;
};
