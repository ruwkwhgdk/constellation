#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimNode_LinkedInputPose.h"
#include "SceneDirectorGaze.generated.h"

class USkeletalMeshComponent;
struct FDirectorGazeProxy;

/** Native evaluation; transient class metadata connects the engine's post-process input pose. */
UCLASS(Transient, NotBlueprintable)
class SCENEDIRECTORRUNTIME_API UDirectorGazeAnimInstance : public UAnimInstance
{
    GENERATED_BODY()
public:
    UPROPERTY(Transient)
    FAnimNode_LinkedInputPose InputPose;

private:
    friend struct FDirectorGazeProxy;
    friend class FDirectorGazeDriver;
    FName HeadBone;
    FVector ForwardAxis = FVector::ForwardVector;
    FVector WorldTarget = FVector::ZeroVector;
    float Weight = 0.f;
    virtual FAnimInstanceProxy* CreateAnimInstanceProxy() override;
    virtual void DestroyAnimInstanceProxy(FAnimInstanceProxy* InProxy) override;
};

/** Game-thread-only scoped ownership of one component's post-process animation. */
class SCENEDIRECTORRUNTIME_API FDirectorGazeDriver
{
public:
    FDirectorGazeDriver() = default;
    ~FDirectorGazeDriver();
    FDirectorGazeDriver(const FDirectorGazeDriver&) = delete;
    FDirectorGazeDriver& operator=(const FDirectorGazeDriver&) = delete;

    bool Initialize(USkeletalMeshComponent* Mesh, FName Bone, FVector ForwardAxis, FString& Error);
    void Update(FVector WorldTarget, float Weight);
    void Reset();

private:
    TWeakObjectPtr<USkeletalMeshComponent> Component;
    TWeakObjectPtr<UClass> InstalledClass;
    TWeakObjectPtr<UClass> PreviousOverride;
    FName HeadBone;
    FVector BoneForwardAxis = FVector::ForwardVector;
    bool bPreviousDisabled = false;
};
