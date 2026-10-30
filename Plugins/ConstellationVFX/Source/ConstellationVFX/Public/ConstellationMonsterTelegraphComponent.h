#pragma once
#include "CoreMinimal.h"
#include "Components/SceneComponent.h"
#include "ConstellationMonsterTelegraphComponent.generated.h"
class UProceduralMeshComponent;
class UMaterialInterface;
class UMaterialInstanceDynamic;

UENUM(BlueprintType)
enum class EMonsterTelegraphPhase : uint8 { Hidden, Preparation, Execution };

USTRUCT(BlueprintType)
struct CONSTELLATIONVFX_API FMonsterTelegraphSettings
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Shape") float Radius=60.f;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Shape") float Thickness=8.f;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Shape") float OutlineWidth=1.5f;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Light") float Brightness=1.f;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Attachment") bool bFaceCamera=true;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Attachment") float CameraOffset=20.f;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Candidate Motion") float PreparationPulseAmount=.06f;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Candidate Motion") float PreparationPulseHz=1.2f;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Candidate Motion") float ExecutionFlashBoost=.25f;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Candidate Motion") float ExecutionFlashDuration=.12f;
    bool IsValid() const;
};

// Cosmetic only. IDs must increase per component lifetime; callbacks cannot revive a stopped ID.
UCLASS(ClassGroup=Effects,meta=(BlueprintSpawnableComponent))
class CONSTELLATIONVFX_API UConstellationMonsterTelegraphComponent : public USceneComponent
{
    GENERATED_BODY()
public:
    UConstellationMonsterTelegraphComponent();
    UPROPERTY(EditAnywhere,BlueprintReadOnly,Category="Telegraph") FMonsterTelegraphSettings Settings;
    UFUNCTION(BlueprintCallable,Category="Telegraph") bool Configure(const FMonsterTelegraphSettings& NewSettings);
    UFUNCTION(BlueprintCallable,Category="Telegraph") bool SetAnchor(USceneComponent* Target,FName Socket,FVector LocalOffset);
    UFUNCTION(BlueprintCallable,Category="Telegraph") bool BeginTelegraph(int64 AttackId);
    UFUNCTION(BlueprintCallable,Category="Telegraph") bool SetPhase(int64 AttackId,EMonsterTelegraphPhase NewPhase);
    UFUNCTION(BlueprintCallable,Category="Telegraph") bool StopTelegraph(int64 AttackId);
    UFUNCTION(BlueprintCallable,Category="Telegraph") void StopAllTelegraphs();
    UFUNCTION(BlueprintPure,Category="Telegraph") EMonsterTelegraphPhase GetPhase()const{return Phase;}
    UFUNCTION(BlueprintPure,Category="Telegraph") int64 GetAttackId()const{return ActiveId;}
    UFUNCTION(BlueprintPure,Category="Telegraph") bool IsShowingTelegraph()const;
    virtual void TickComponent(float Delta,ELevelTick TickType,FActorComponentTickFunction* TickFunction) override;
protected:
    virtual void OnRegister() override;
    virtual void OnUnregister() override;
    virtual void OnAttachmentChanged() override;
    virtual void OnComponentDestroyed(bool bDestroyingHierarchy) override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
private:
    UPROPERTY() TObjectPtr<UMaterialInterface> RingMaterial;
    UPROPERTY(Transient,DuplicateTransient) TObjectPtr<UProceduralMeshComponent> Ring;
    UPROPERTY(Transient,DuplicateTransient) TObjectPtr<UMaterialInstanceDynamic> DynamicMaterial;
    EMonsterTelegraphPhase Phase=EMonsterTelegraphPhase::Hidden;
    int64 ActiveId=0,LastId=0;
    float PhaseAge=0.f;
    TWeakObjectPtr<USceneComponent> Anchor;
    bool bHasAnchor=false,bUpdatingAnchor=false;
    bool IsAnchorAvailable()const;
    void BuildRing();
    void UpdatePresentation();
};
