#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "SceneDirectorGaze.h"
#include "Animation/AnimSequence.h"
#include "Animation/SkeletalMeshActor.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "Engine/Engine.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorGazePoseTest, "Constellation.SceneDirector.GazePoseAndRestore", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FDirectorGazePoseTest::RunTest(const FString&)
{
    auto* Source = LoadObject<USkeletalMesh>(nullptr, TEXT("/Game/Constellation/Characters/Heroine/Refined/SK_player_heroine_new_RunPreview.SK_player_heroine_new_RunPreview"));
    auto* Animation = LoadObject<UAnimSequence>(nullptr, TEXT("/Game/Constellation/Characters/Heroine/Refined/Animations/AS_player_heroine_new_Run_Soft.AS_player_heroine_new_Run_Soft"));
    if (!TestNotNull(TEXT("Fixture mesh"), Source) || !TestNotNull(TEXT("Fixture animation"), Animation)) return false;
    const auto AssetPostProcess = Source->GetPostProcessAnimBlueprint();
    // A transient copy isolates the fixture from any production post-process graph.
    auto* MeshAsset = DuplicateObject<USkeletalMesh>(Source, GetTransientPackage());
    MeshAsset->SetPostProcessAnimBlueprint(nullptr);
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
    GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());
    auto MakeMesh = [&]()
    {
        auto* Actor = World->SpawnActor<ASkeletalMeshActor>();
        auto* Mesh = Actor->GetSkeletalMeshComponent();
        Mesh->SetSkeletalMeshAsset(MeshAsset);
        Mesh->SetAnimationMode(EAnimationMode::AnimationSingleNode);
        Mesh->SetAnimation(Animation);
        Mesh->SetPosition(.25f, false);
        Mesh->SetPlayRate(0.f);
        Mesh->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
        return Mesh;
    };
    auto Evaluate = [](USkeletalMeshComponent* Mesh)
    {
        Mesh->TickAnimation(0.f, false);
        Mesh->RefreshBoneTransforms();
        Mesh->CompleteParallelAnimationEvaluation(true);
    };
    auto* Mesh = MakeMesh();
    auto* Other = MakeMesh();
    Evaluate(Mesh);
    Evaluate(Other);
    const int32 HeadIndex = Mesh->GetBoneIndex(TEXT("head"));
    if (!TestTrue(TEXT("Head exists"), HeadIndex != INDEX_NONE))
    {
        GEngine->DestroyWorldContext(World); World->DestroyWorld(false); return false;
    }
    UAnimInstance* OriginalMainInstance = Mesh->GetAnimInstance();
    const auto OriginalPose = Mesh->GetBoneSpaceTransforms();
    const auto OtherPose = Other->GetBoneSpaceTransforms();
    const FTransform InitialHead = Mesh->GetBoneTransform(HeadIndex);
    const FVector Forward = InitialHead.GetRotation().RotateVector(FVector::ForwardVector);
    FVector Side = FVector::CrossProduct(Forward, FVector::UpVector).GetSafeNormal();
    if (Side.IsNearlyZero()) Side = FVector::CrossProduct(Forward, FVector::RightVector).GetSafeNormal();
    const FVector Target = InitialHead.GetLocation() + Side * 500.f;
    FString Error;
    Mesh->SetDisablePostProcessBlueprint(true);
    {
        FDirectorGazeDriver Driver;
        TestFalse(TEXT("Missing bone rejected"), Driver.Initialize(Mesh, TEXT("missing_gaze_bone"), FVector::ForwardVector, Error));
        TestFalse(TEXT("Zero axis rejected"), Driver.Initialize(Mesh, TEXT("head"), FVector::ZeroVector, Error));
        if (TestTrue(TEXT("Install gaze"), Driver.Initialize(Mesh, TEXT("head"), FVector::ForwardVector, Error)))
        {
            TestEqual(TEXT("Gaze preserves main instance identity"), Mesh->GetAnimInstance(), OriginalMainInstance);
            TestFalse(TEXT("Gaze enables postprocess"), Mesh->GetDisablePostProcessBlueprint());
            TestNotNull(TEXT("Engine sees native input pose"), Mesh->GetPostProcessInstance()->GetLinkedInputPoseNode());
            FDirectorGazeDriver ConflictingDriver;
            TestFalse(TEXT("Second owner rejected"), ConflictingDriver.Initialize(Mesh, TEXT("head"), FVector::ForwardVector, Error));
            Driver.Update(Target, 0.f);
            Evaluate(Mesh);
            TestTrue(TEXT("Zero weight preserves animated head"), Mesh->GetBoneSpaceTransforms()[HeadIndex].Equals(OriginalPose[HeadIndex], .001f));
            Driver.Update(Target, 1.f);
            Evaluate(Mesh);
            const FQuat FullRotation = Mesh->GetBoneTransform(HeadIndex).GetRotation();
            const double FullAngle = FMath::RadiansToDegrees(InitialHead.GetRotation().AngularDistance(FullRotation));
            TestTrue(TEXT("Head visibly rotates and clamps to 70 degrees"), FMath::IsNearlyEqual(FullAngle, 70.0, .2));
            bool bOtherBonesPreserved = true;
            const auto& GazePose = Mesh->GetBoneSpaceTransforms();
            for (int32 Index = 0; Index < OriginalPose.Num(); ++Index)
                if (Index != HeadIndex && !GazePose[Index].Equals(OriginalPose[Index], .001f)) bOtherBonesPreserved = false;
            TestTrue(TEXT("Underlying animation retained on every other local bone"), bOtherBonesPreserved);
            Driver.Update(Target, .5f);
            Evaluate(Mesh);
            const double HalfAngle = FMath::RadiansToDegrees(InitialHead.GetRotation().AngularDistance(Mesh->GetBoneTransform(HeadIndex).GetRotation()));
            TestTrue(TEXT("Caller weight blends to 35 degrees"), FMath::IsNearlyEqual(HalfAngle, 35.0, .2));
            Evaluate(Other);
            TestTrue(TEXT("Other component head unaffected"), Other->GetBoneSpaceTransforms()[HeadIndex].Equals(OtherPose[HeadIndex], .001f));
            TestNull(TEXT("Other component override unaffected"), Other->OverridePostProcessAnimBP.Get());
        }
        else AddError(Error);
    }
    TestEqual(TEXT("Reset preserves main instance identity"), Mesh->GetAnimInstance(), OriginalMainInstance);
    TestNull(TEXT("Destructor restores original override"), Mesh->OverridePostProcessAnimBP.Get());
    TestTrue(TEXT("Destructor restores disabled flag"), Mesh->GetDisablePostProcessBlueprint());
    Evaluate(Mesh);
    TestTrue(TEXT("Original head animation restored"), Mesh->GetBoneSpaceTransforms()[HeadIndex].Equals(OriginalPose[HeadIndex], .001f));
    TestEqual(TEXT("Shared asset postprocess never changed"), Source->GetPostProcessAnimBlueprint(), AssetPostProcess);
    Mesh->SetOverridePostProcessAnimBP(UAnimInstance::StaticClass());
    {
        FDirectorGazeDriver Driver;
        TestFalse(TEXT("Existing incompatible graph rejected"), Driver.Initialize(Mesh, TEXT("head"), FVector::ForwardVector, Error));
    }
    TestEqual(TEXT("Rejected graph preserved"), Mesh->OverridePostProcessAnimBP.Get(), UAnimInstance::StaticClass());
    Mesh->SetOverridePostProcessAnimBP(nullptr);
    GEngine->DestroyWorldContext(World);
    World->DestroyWorld(false);
    return true;
}
#endif
