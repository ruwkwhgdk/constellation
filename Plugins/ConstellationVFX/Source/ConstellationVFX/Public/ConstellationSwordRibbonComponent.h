#pragma once
#include "CoreMinimal.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "ProceduralMeshComponent.h"
#include "ConstellationSwordRibbonComponent.generated.h"

// Preserve the serialized ISM base used by existing maps. A transient child renders
// the connected strip; the wrapper never renders static-mesh instances.
UCLASS(ClassGroup=Effects)
class CONSTELLATIONVFX_API UConstellationSwordRibbonComponent : public UInstancedStaticMeshComponent
{
    GENERATED_BODY()
public:
    UConstellationSwordRibbonComponent(const FObjectInitializer& ObjectInitializer);
    void Configure(FLinearColor Color);
    void AddTip(FVector WorldTip,float Delta);
    void ResetTrail();
    // Logical sampled spans, independent of the smooth mesh tessellation.
    int32 GetSegmentCount() const { return ActiveSegments; }
    FProcMeshSection* GetProcMeshSection(int32 SectionIndex) const;
protected:
    virtual void OnRegister() override;
    virtual void OnUnregister() override;
    virtual void OnComponentDestroyed(bool bDestroyingHierarchy) override;
private:
    void EnsureRibbonMesh();
    UPROPERTY(Transient, DuplicateTransient) TObjectPtr<UProceduralMeshComponent> RibbonMesh;
    struct FTipSample { FVector Position;float Age=0.f; };
    TArray<FTipSample> Samples;
    int32 ActiveSegments=0;
};
