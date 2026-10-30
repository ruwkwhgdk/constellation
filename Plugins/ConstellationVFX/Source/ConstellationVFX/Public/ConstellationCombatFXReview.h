#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "ConstellationCombatFXReview.generated.h"
class UConstellationSwordRibbonComponent;

// Explicit gallery-only art review. Synthetic arcs are not approved attack motions.
UCLASS()
class CONSTELLATIONVFX_API AConstellationCombatFXReview : public AActor
{
    GENERATED_BODY()
public:
    AConstellationCombatFXReview();
    virtual void BeginPlay() override;
    virtual void Tick(float Delta) override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
private:
    UPROPERTY() TArray<TObjectPtr<UConstellationSwordRibbonComponent>> Ribbons;
    UPROPERTY() TObjectPtr<class ACameraActor> Camera;
    UPROPERTY() TSubclassOf<class AHUD> PreviousHUD;
    TArray<TWeakObjectPtr<AActor>> HiddenActors;
    float Clock=0.f,PreviousPhase=2.f;
    bool bCapture=false,bTrailsCaptured=false,bContactsCaptured=false,bHUDSwapped=false;
    void Contacts();
};
