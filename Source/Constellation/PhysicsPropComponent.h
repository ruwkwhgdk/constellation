#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Engine/DataTable.h"
#include "PhysicsPropComponent.generated.h"

class UPhysicalMaterial;
class UPrimitiveComponent;

USTRUCT(BlueprintType)
struct CONSTELLATION_API FPhysicsPropRow : public FTableRowBase
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Physics", meta=(ClampMin="0.01"))
    float MassKg = 5.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Physics", meta=(ClampMin="0"))
    float LinearDamping = .01f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Physics", meta=(ClampMin="0"))
    float AngularDamping = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Physics")
    bool bSimulatePhysics = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Physics")
    bool bEnableGravity = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Physics")
    TObjectPtr<UPhysicalMaterial> PhysicalMaterial = nullptr;
};

// Applies authored startup state once; gameplay owns subsequent physics transitions.
UCLASS(Blueprintable, ClassGroup=(Physics), meta=(BlueprintSpawnableComponent))
class CONSTELLATION_API UPhysicsPropComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Physics|Data", meta=(RowType="/Script/Constellation.PhysicsPropRow"))
    FDataTableRowHandle PhysicsRow;
    // Optional component name for multi-mesh props. Empty uses the root primitive.
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Physics|Data")
    FName MeshComponentName;
    UFUNCTION(BlueprintCallable, Category="Physics|Data")
    bool ApplyInitialSettings();
protected:
    virtual void BeginPlay() override;
private:
    bool bApplied = false;
};
