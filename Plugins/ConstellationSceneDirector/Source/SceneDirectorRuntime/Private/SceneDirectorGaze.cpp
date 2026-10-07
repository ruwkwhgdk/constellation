#include "SceneDirectorGaze.h"
#include "Animation/AnimBlueprintGeneratedClass.h"
#include "Animation/AnimInstanceProxy.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "UObject/UnrealType.h"

struct FDirectorGazeProxy : FAnimInstanceProxy
{
    explicit FDirectorGazeProxy(UAnimInstance* Instance) : FAnimInstanceProxy(Instance) {}

    virtual void Initialize(UAnimInstance* Instance) override
    {
        Input = &CastChecked<UDirectorGazeAnimInstance>(Instance)->InputPose;
        FAnimInstanceProxy::Initialize(Instance);
    }

    virtual void PreUpdate(UAnimInstance* Instance, float DeltaSeconds) override
    {
        FAnimInstanceProxy::PreUpdate(Instance, DeltaSeconds);
        const auto* Gaze = CastChecked<UDirectorGazeAnimInstance>(Instance);
        const auto* Mesh = Gaze->GetSkelMeshComponent();
        BoneIndex = Mesh ? Mesh->GetBoneIndex(Gaze->HeadBone) : INDEX_NONE;
        Target = Mesh ? Mesh->GetComponentTransform().InverseTransformPosition(Gaze->WorldTarget) : FVector::ZeroVector;
        Forward = Gaze->ForwardAxis;
        Weight = Gaze->Weight;
    }

    virtual bool Evaluate(FPoseContext& Output) override
    {
        // This pointer refers to the instance-owned node, not live UObject data. The engine fills
        // its cached pose in this same evaluation job before invoking our proxy.
        Input->Evaluate_AnyThread(Output);
        if (Weight <= 0.f || BoneIndex == INDEX_NONE) return true;
        const FBoneContainer& Bones = Output.Pose.GetBoneContainer();
        const FCompactPoseBoneIndex Head = Bones.MakeCompactPoseIndex(FMeshPoseBoneIndex(BoneIndex));
        if (Head == INDEX_NONE) return true; // Bone stripped at this LOD.
        FCSPose<FCompactPose> ComponentPose;
        ComponentPose.InitPose(Output.Pose);
        const FTransform HeadTransform = ComponentPose.GetComponentSpaceTransform(Head);
        const FVector Desired = (Target - HeadTransform.GetLocation()).GetSafeNormal();
        if (Desired.IsNearlyZero()) return true;
        const FVector Current = HeadTransform.GetRotation().RotateVector(Forward).GetSafeNormal();
        FQuat Delta = FQuat::FindBetweenNormals(Current, Desired);
        const double Angle = Delta.GetAngle();
        const double Limit = FMath::DegreesToRadians(70.0);
        const double Alpha = Weight * (Angle > Limit ? Limit / Angle : 1.0);
        Delta = FQuat::Slerp(FQuat::Identity, Delta, Alpha).GetNormalized();
        const FCompactPoseBoneIndex Parent = Bones.GetParentBoneIndex(Head);
        const FQuat ParentRotation = Parent != INDEX_NONE
            ? ComponentPose.GetComponentSpaceTransform(Parent).GetRotation() : FQuat::Identity;
        // Only replace the head's local rotation. Translation, scale, other local bones,
        // curves and custom attributes remain the animation's current input values.
        Output.Pose[Head].SetRotation((ParentRotation.Inverse() * Delta * HeadTransform.GetRotation()).GetNormalized());
        return true;
    }

    FAnimNode_LinkedInputPose* Input = nullptr;
    int32 BoneIndex = INDEX_NONE;
    FVector Target = FVector::ZeroVector;
    FVector Forward = FVector::ForwardVector;
    float Weight = 0.f;
};

FAnimInstanceProxy* UDirectorGazeAnimInstance::CreateAnimInstanceProxy() { return new FDirectorGazeProxy(this); }
void UDirectorGazeAnimInstance::DestroyAnimInstanceProxy(FAnimInstanceProxy* Proxy) { delete Proxy; }

namespace
{
UClass* MakeGazeClass()
{
    // GetLinkedInputPoseNode is nonvirtual and its proxy pointer is private in UE5.8.
    // Supply its public animation-function metadata instead of reaching into engine internals.
    // This transient class has no script/compiled graph: evaluation is entirely native above.
    auto* Class = NewObject<UAnimBlueprintGeneratedClass>(GetTransientPackage(), NAME_None, RF_Transient);
    Class->SetSuperStruct(UDirectorGazeAnimInstance::StaticClass());
    Class->ClassFlags |= CLASS_Transient;
    Class->Bind();
    Class->StaticLink(true);
    FAnimBlueprintFunction Function(TEXT("AnimGraph"));
    Function.InputPoseNames.Add(FAnimNode_LinkedInputPose::DefaultInputPoseName);
    Function.InputPoseNodeProperties.Add(FindFProperty<FStructProperty>(UDirectorGazeAnimInstance::StaticClass(), GET_MEMBER_NAME_CHECKED(UDirectorGazeAnimInstance, InputPose)));
    Class->AnimBlueprintFunctions.Add(Function);
    Class->GetDefaultObject();
    Class->UpdateCustomPropertyListForPostConstruction();
    return Class;
}
}

FDirectorGazeDriver::~FDirectorGazeDriver() { Reset(); }

bool FDirectorGazeDriver::Initialize(USkeletalMeshComponent* Mesh, FName Bone, FVector ForwardAxis, FString& Error)
{
    check(IsInGameThread());
    Reset();
    Error.Reset();
    if (!IsValid(Mesh) || !Mesh->GetSkeletalMeshAsset() || !Mesh->IsRegistered())
    {
        Error = TEXT("Gaze requires a registered skeletal mesh component with a mesh asset.");
        return false;
    }
    if (Bone.IsNone() || Mesh->GetBoneIndex(Bone) == INDEX_NONE)
    {
        Error = FString::Printf(TEXT("Gaze bone '%s' is missing on '%s'."), *Bone.ToString(), *Mesh->GetName());
        return false;
    }
    if (ForwardAxis.ContainsNaN() || ForwardAxis.IsNearlyZero())
    {
        Error = TEXT("Gaze forward axis must be a finite nonzero bone-local vector.");
        return false;
    }
    if (Mesh->GetPostProcessAnimBPClassToBeUsed())
    {
        Error = FString::Printf(TEXT("'%s' already has a post-process animation class. Use a compatible character without an existing post-process graph for Scene Director gaze."), *Mesh->GetName());
        return false;
    }
    Mesh->CompleteParallelAnimationEvaluation(true);
    Component = Mesh;
    PreviousOverride = Mesh->OverridePostProcessAnimBP.Get();
    bPreviousDisabled = Mesh->GetDisablePostProcessBlueprint();
    HeadBone = Bone;
    BoneForwardAxis = ForwardAxis.GetSafeNormal();
    InstalledClass = MakeGazeClass();
    // The default setter rebuilds the primary single-node instance too. Install only
    // our post-process instance so its playback position and linked graphs survive.
    Mesh->SetOverridePostProcessAnimBP(InstalledClass.Get(), false);
    Mesh->SetDisablePostProcessBlueprint(false);
    auto* Instance = NewObject<UDirectorGazeAnimInstance>(Mesh, InstalledClass.Get());
    Mesh->PostProcessAnimInstance = Instance;
    Instance->InitializeAnimation();
    if (Mesh->HasBegunPlay())
    {
        Instance->NativeBeginPlay();
        Instance->BlueprintBeginPlay();
    }
    if (FAnimNode_LinkedInputPose* Input = Instance->GetLinkedInputPoseNode())
    {
        const FBoneContainer& Bones = Instance->GetRequiredBones();
        if (Bones.IsValid()) Input->CachedInputPose.SetBoneContainer(&Bones);
        Input->bIsCachedInputPoseInitialized = false;
    }
    if (!Cast<UDirectorGazeAnimInstance>(Mesh->GetPostProcessInstance()))
    {
        Error = TEXT("Unable to initialize Scene Director gaze post-process animation; verify the mesh has a skeleton and animation is enabled.");
        Reset();
        return false;
    }
    Update(FVector::ZeroVector, 0.f);
    return true;
}

void FDirectorGazeDriver::Update(FVector WorldTarget, float Weight)
{
    check(IsInGameThread());
    if (auto* Mesh = Component.Get(); Mesh && Mesh->OverridePostProcessAnimBP.Get() == InstalledClass.Get())
    {
        if (auto* Instance = Cast<UDirectorGazeAnimInstance>(Mesh->GetPostProcessInstance()))
        {
            Instance->HeadBone = HeadBone;
            Instance->ForwardAxis = BoneForwardAxis;
            Instance->WorldTarget = WorldTarget.ContainsNaN() ? FVector::ZeroVector : WorldTarget;
            Instance->Weight = WorldTarget.ContainsNaN() || !FMath::IsFinite(Weight) ? 0.f : FMath::Clamp(Weight, 0.f, 1.f);
        }
    }
}

void FDirectorGazeDriver::Reset()
{
    check(IsInGameThread());
    if (auto* Mesh = Component.Get(); Mesh && Mesh->OverridePostProcessAnimBP.Get() == InstalledClass.Get())
    {
        Mesh->CompleteParallelAnimationEvaluation(true);
        if (UAnimInstance* Instance = Mesh->GetPostProcessInstance()) Instance->UninitializeAnimation();
        Mesh->PostProcessAnimInstance = nullptr;
        Mesh->SetOverridePostProcessAnimBP(PreviousOverride.Get(), false);
        Mesh->SetDisablePostProcessBlueprint(bPreviousDisabled);
    }
    Component.Reset();
    InstalledClass.Reset();
    PreviousOverride.Reset();
}
