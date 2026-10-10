#include "LittleGirlLocomotionComponent.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Animation/BlendSpace.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"

ULittleGirlLocomotionComponent::ULittleGirlLocomotionComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickGroup = TG_PostPhysics;
}

void ULittleGirlLocomotionComponent::ResumeLocomotion()
{
    auto* Character = Cast<ACharacter>(GetOwner());
    if (!Character || !LocomotionBlendSpace || !PrototypeMesh) return;
    auto* Mesh = Character->GetMesh();
    if (!bConfigured)
    {
        Mesh->SetSkeletalMesh(PrototypeMesh);
        Mesh->EmptyOverrideMaterials();
        Mesh->SetRelativeScale3D(FVector(1.35424f));
        Mesh->SetRelativeRotation(FRotator::ZeroRotator);
        RestMeshLocation = FVector(0.f, 0.f, -66.4564f);
        Mesh->SetRelativeLocation(RestMeshLocation);
        Character->GetCapsuleComponent()->SetCapsuleSize(26.f, 66.4564f);
        auto* Movement = Character->GetCharacterMovement();
        // Preserve a speed already selected by NPC activation or AI startup.
        Movement->MaxWalkSpeed = FMath::Min(Movement->MaxWalkSpeed, 98.f);
        Movement->MaxAcceleration = 256.f;
        Movement->BrakingDecelerationWalking = 512.f;
        Movement->MaxStepHeight = 18.f;
        Movement->bOrientRotationToMovement = true;
        Movement->RotationRate = FRotator(0.f, 360.f, 0.f);
        Character->bUseControllerRotationYaw = false;
        bConfigured = true;
    }
    bFirstTick = false;
    bSuspended = false;
    Mesh->PlayAnimation(LocomotionBlendSpace, true);
}

void ULittleGirlLocomotionComponent::SuspendLocomotion()
{
    bFirstTick = false;
    bSuspended = true;
}

void ULittleGirlLocomotionComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    // Wait until the owner's Blueprint BeginPlay has completed.
    if (bFirstTick)
    {
        bFirstTick = false;
        if (bStartAutomatically) ResumeLocomotion();
    }
    auto* Character = Cast<ACharacter>(GetOwner());
    if (!Character || bSuspended) return;
    LocomotionSpeed = Character->GetVelocity().Size2D();
    auto* Mesh = Character->GetMesh();
    auto* Instance = Mesh->GetSingleNodeInstance();
    // A sequence or event that takes animation ownership must keep it until
    // gameplay explicitly calls ResumeLocomotion.
    if (!Instance || Instance->GetCurrentAsset() != LocomotionBlendSpace) return;
    Instance->SetBlendSpacePosition(FVector(LocomotionSpeed, 0.f, 0.f));
    auto* Movement = Character->GetCharacterMovement();
    if (Movement->IsMovingOnGround() && Movement->CurrentFloor.IsWalkableFloor())
    {
        const float Gap = FMath::Clamp(Movement->CurrentFloor.GetDistanceToFloor(), 0.f, 2.4f);
        Mesh->SetRelativeLocation(RestMeshLocation - FVector(0.f, 0.f, Gap));
    }
}
