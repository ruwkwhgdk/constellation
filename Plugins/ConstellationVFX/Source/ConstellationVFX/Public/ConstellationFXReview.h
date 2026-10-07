#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "ConstellationFXReview.generated.h"
class ACameraActor;
class AConstellationGlass;
UCLASS()
class CONSTELLATIONVFX_API AConstellationFXReview : public AActor {
 GENERATED_BODY()
public:
 AConstellationFXReview();
 virtual void BeginPlay() override;
 virtual void Tick(float Delta) override;
 UPROPERTY(EditAnywhere,Category="Review") bool bAutoReview=false;
 UPROPERTY(EditAnywhere,Category="Review") bool bEnvironmentOnly=false;
private:
 float Clock=0,StageClock=0;int32 Stage=-1;bool bCaptured=false,bAutomated=false;
 TArray<double> FrameMs,BaselineMs;
 bool bBenchmark=false,bGlassReview=false,bGlassInvoked=false,bGalleryGlassPassed=false;float StressClock=0;int32 PeakEffects=0,PeakParticles=0;
 UPROPERTY() TObjectPtr<AActor> LegacyGlass;
 UPROPERTY() TObjectPtr<class AConstellationGlassRelay> GlassRelay;
 UPROPERTY() TObjectPtr<ACameraActor> Camera;
 UPROPERTY() TObjectPtr<AConstellationGlass> Glass;
 void StartStage();void FinishReview();
};
