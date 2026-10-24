#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "TimerManager.h"
#include "StarlightPlayerHUDWidget.generated.h"

class UCombatAbilitySystem;
class UTexture2D;
UCLASS()
class CONSTELLATION_API UStarlightPlayerHUDWidget : public UUserWidget
{
 GENERATED_BODY()
public:
 UStarlightPlayerHUDWidget(const FObjectInitializer& ObjectInitializer);
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Starlight HUD",meta=(ClampMin="0",ClampMax="1")) float LowHealthThreshold=.25f;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Starlight HUD",meta=(ClampMin=".1")) float LowHealthPulseSeconds=2.f;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Starlight HUD") FVector2D SafePadding=FVector2D(40,28);
 UFUNCTION(BlueprintPure,Category="Starlight HUD") float GetHealthRatio() const {return HealthRatio;}
 UFUNCTION(BlueprintPure,Category="Starlight HUD") float GetStaminaRatio() const {return StaminaRatio;}
 UFUNCTION(BlueprintPure,Category="Starlight HUD") float GetDamageTrailRatio() const {return FMath::Max(HealthRatio,DamageTrailRatio);}
 UFUNCTION(BlueprintPure,Category="Starlight HUD") bool IsFailureFeedbackActive() const {return FailureElapsed>=0&&FailureElapsed<.35f;}
 UFUNCTION(BlueprintPure,Category="Starlight HUD") FVector2D GetStarOffset() const;
 UFUNCTION(BlueprintPure,Category="Starlight HUD") FLinearColor GetStarColor() const;
 UFUNCTION(BlueprintCallable,Category="Starlight HUD") static void NotifyDamage(AActor* Source);
 UFUNCTION(BlueprintCallable,Category="Starlight HUD") static void NotifyStaminaRejected(AActor* Source);
 UFUNCTION(BlueprintCallable,Category="Starlight HUD") static void NotifyLegacySprintRejected(AActor* Source);
 void AdvanceVisuals(float DeltaSeconds);
 UTexture2D* GetNebulaTexture() const {return NebulaTexture;}
protected:
 virtual TSharedRef<SWidget> RebuildWidget() override;
 virtual void NativeConstruct() override;
 virtual void NativeDestruct() override;
private:
 friend class FStarlightHUDResourceTest;
 void CollapseLegacyBars();
 void DetachLegacyBarBinding(UObject* Stats);
 void TickVisuals();
 void RebindResources();
 void UnbindResources();
 void SampleResources(float DeltaSeconds);
 void RecordDamage();
 void StartFailureFeedback();
 static UObject* FindLegacyStats(AActor* Actor);
 static float ReadNumber(const UObject* Object,FName PropertyName,float DefaultValue=0.f);
 UPROPERTY() TObjectPtr<UTexture2D> NebulaTexture;
 TWeakObjectPtr<APawn> ResourcePawn;
 TWeakObjectPtr<UObject> LegacyStats;
 TWeakObjectPtr<UObject> LegacyBindingStats;
 TWeakObjectPtr<UCombatAbilitySystem> Combat;
 FDelegateHandle DamageHandle,RejectedHandle;
 FTimerHandle VisualTimer;
 double LastTickTime=0;
 float HealthRatio=1,StaminaRatio=1,DamageTrailRatio=1,TrailStart=1,TrailElapsed=1,LastMaxHealth=0;
 float VisualTime=0,FailureElapsed=-1,FailureCooldown=0;
 bool bActive=false,bHaveSample=false,bPendingDamage=false;
 static TArray<TWeakObjectPtr<UStarlightPlayerHUDWidget>> ActiveHUDs;
};
