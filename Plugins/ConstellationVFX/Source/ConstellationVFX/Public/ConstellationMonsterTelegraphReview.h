#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "ConstellationMonsterTelegraphReview.generated.h"
class UConstellationMonsterTelegraphComponent;
class USkeletalMeshComponent;
class UMaterialInstanceDynamic;
class ACameraActor;

// Standalone visual fixture. Its scripted steps are not combat timing or an integration adapter.
UCLASS()
class CONSTELLATIONVFX_API AConstellationMonsterTelegraphReview : public AActor
{
    GENERATED_BODY()
public:
    AConstellationMonsterTelegraphReview();
    virtual void BeginPlay()override;
    virtual void Tick(float Delta)override;
    virtual void EndPlay(const EEndPlayReason::Type Reason)override;
private:
    UPROPERTY() TArray<TObjectPtr<UConstellationMonsterTelegraphComponent>> Telegraphs;
    UPROPERTY() TArray<TObjectPtr<USkeletalMeshComponent>> Monsters;
    UPROPERTY() TObjectPtr<ACameraActor> Camera;
    UPROPERTY() TObjectPtr<UMaterialInstanceDynamic> Backdrop;
    UPROPERTY() TArray<TObjectPtr<AActor>> Props;
    TArray<TWeakObjectPtr<AActor>> HiddenActors;
    FString OutputDirectory;
    float Clock=0,StageAge=0;
    int32 Stage=-1;
    int64 PreviewId=0;
    bool bCapture=false,bCaptured=false,bHUDHidden=false;
    void StartStage(int32 Index);
};
