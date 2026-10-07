#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/HUD.h"
#include "ConstellationFXGallery.generated.h"
UCLASS()
class CONSTELLATIONVFX_API AConstellationFXGallery : public AActor {
 GENERATED_BODY()
public:
 AConstellationFXGallery();
 virtual void BeginPlay() override;
 virtual void Tick(float Delta) override;
 void SelectStation(int32 Index, bool Frame=true);
 void Replay();
 FVector StationPosition(int32 Index) const;
 int32 Selected=0;
 int32 HitDirection=0;
 bool bRepeat=true;
 float ReadyTime=0;
 static const TCHAR* StationName(int32 Index);
private:
 UPROPERTY() TObjectPtr<class AConstellationGlass> Glass;
 UPROPERTY() TObjectPtr<class UStaticMeshComponent> Sword;
 UPROPERTY() TObjectPtr<class UConstellationSwordRibbonComponent> Ribbon;
 UPROPERTY() TObjectPtr<class UNiagaraComponent> Trail;
 UPROPERTY() TArray<TObjectPtr<UObject>> RetainedAssets;
 float ReplayClock=0,SlashAge=10,Clock=0,ProbeClock=0;
 bool bProbe=false,bCapture=false,bProbeCaptured=false,bReactionCapture=false;
 int32 ReactionCaptureStage=-1,ReactionCaptureFrame=0;
 FVector ProbeStart=FVector::ZeroVector;
 bool bMovementVerified=false;
 int32 ProbeStage=-1,ReplayCount=0;
 TArray<double> GlassFrames;
 UPROPERTY() TObjectPtr<class USkeletalMeshComponent> ReactionMesh;
 UPROPERTY() TObjectPtr<class UAnimationAsset> ReactionBase;
 float ReactionAge=1,ReactionBaseTime=0;
 void RestoreReaction();
 void PreviewReaction();
 void FrameStation();
};
UCLASS()
class CONSTELLATIONVFX_API AConstellationFXGalleryHUD : public AHUD {
 GENERATED_BODY()
 virtual void DrawHUD() override;
};
UCLASS()
class CONSTELLATIONVFX_API AConstellationFXGalleryMode : public AGameModeBase {
 GENERATED_BODY()
public:
 AConstellationFXGalleryMode();
};
