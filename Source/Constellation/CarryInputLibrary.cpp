#include "CarryInputLibrary.h"
#include "CarryComponent.h"
#include "PlayerFallComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/Controller.h"
#include "UObject/UnrealType.h"
#include "Animation/AnimInstance.h"
#include "Components/SkeletalMeshComponent.h"

bool UCarryInputLibrary::RouteCarryInput(AActor* Actor,FName Action,FName Phase)
{
    if(!IsValid(Actor)) return false;
    // Release/cancel paths must remain available so held inputs cannot stick.
    if(const auto* Fall=Actor->FindComponentByClass<UPlayerFallComponent>())
    {
        if(Fall->IsLandingLocked()&&Action==TEXT("IA_Attack")&&(Phase==TEXT("Completed")||Phase==TEXT("Canceled")))
        {
            if(auto* Carry=Actor->FindComponentByClass<UCarryComponent>())Carry->CancelAim();
            return true;
        }
        if(Fall->IsLandingLocked()&&Action!=TEXT("IA_Look")&&Action!=TEXT("IA_Debug")
            &&Phase!=TEXT("Completed")&&Phase!=TEXT("Canceled")) return true;
    }
    UCarryComponent* Carry=Actor->FindComponentByClass<UCarryComponent>(); if(!Carry) return false;
    if(Action==TEXT("IA_Move")) return !Carry->AllowsWalking();
    if(Action==TEXT("IA_Interact"))
    {
        if(!Carry->BlocksOtherActions())
        {
            const ACharacter* C=Cast<ACharacter>(Actor);
            if(C&&C->GetController()&&C->GetController()->IsMoveInputIgnored()) return true;
            for(FName Name : {FName("IsAttacking"),FName("IsPushing"),FName("IsClimbing"),FName("bIsJumping")})
                if(const FBoolProperty* Property=FindFProperty<FBoolProperty>(Actor->GetClass(),Name))
                    if(Property->GetPropertyValue_InContainer(Actor)) return true;
        }
        return Carry->HandleInteract();
    }
    if(Action==TEXT("IA_Attack")&&Carry->BlocksOtherActions())
    {
        if(Phase==TEXT("Started")) Carry->BeginAim();
        else if(Phase==TEXT("Completed")) Carry->CommitThrow();
        else if(Phase==TEXT("Canceled")) Carry->CancelAim();
        return true;
    }
    return Carry->BlocksOtherActions();
}
void UCarryInputLibrary::AbortActorCarry(AActor* Actor)
{
    if(IsValid(Actor)) if(UCarryComponent* Carry=Actor->FindComponentByClass<UCarryComponent>()) Carry->AbortCarry();
}
float UCarryInputLibrary::CarryIKAlpha(UAnimInstance* AnimInstance)
{
    AActor* Actor=AnimInstance?AnimInstance->GetOwningActor():nullptr;
    const UCarryComponent* Carry=Actor?Actor->FindComponentByClass<UCarryComponent>():nullptr;
    if(Carry&&Carry->GetFittedPickupAlpha()>0.f) return Carry->GetFittedPickupAlpha();
    if(Carry&&Carry->GetFittedPlaceAlpha()>0.f) return Carry->GetFittedPlaceAlpha();
    return Carry&&(Carry->State==ECarryState::Carrying||Carry->State==ECarryState::Aiming)?1.f:0.f;
}
FVector UCarryInputLibrary::CarryGrip(UAnimInstance* AnimInstance,bool bLeft)
{
    if(!AnimInstance||!AnimInstance->GetSkelMeshComponent()||!AnimInstance->GetOwningActor()) return FVector::ZeroVector;
    const UCarryComponent* Carry=AnimInstance->GetOwningActor()->FindComponentByClass<UCarryComponent>();
    return Carry?AnimInstance->GetSkelMeshComponent()->GetComponentTransform().InverseTransformPosition(Carry->GetHandGrip(bLeft).GetLocation()):FVector::ZeroVector;
}
FVector UCarryInputLibrary::CarryElbow(UAnimInstance* AnimInstance,bool bLeft)
{
    if(!AnimInstance||!AnimInstance->GetSkelMeshComponent()||!AnimInstance->GetOwningActor()) return FVector::ZeroVector;
    const UCarryComponent* Carry=AnimInstance->GetOwningActor()->FindComponentByClass<UCarryComponent>();
    if(Carry&&Carry->UsesFittedCarry())
    {
        const USkeletalMeshComponent* Mesh=AnimInstance->GetSkelMeshComponent();
        return Mesh->GetComponentTransform().InverseTransformPosition(Mesh->GetSocketLocation(bLeft?TEXT("lowerarm_l"):TEXT("lowerarm_r")));
    }
    const FVector World=AnimInstance->GetOwningActor()->GetActorTransform().TransformPosition(FVector(0,bLeft?-30:30,10));
    return AnimInstance->GetSkelMeshComponent()->GetComponentTransform().InverseTransformPosition(World);
}

float UCarryInputLibrary::CarryLeftIKAlpha(UAnimInstance* AnimInstance)
{
    const AActor* Actor=AnimInstance?AnimInstance->GetOwningActor():nullptr;
    const UCarryComponent* Carry=Actor?Actor->FindComponentByClass<UCarryComponent>():nullptr;
    if(Carry&&Carry->UsesFittedCarry()&&Carry->State==ECarryState::Throwing&&Carry->GetHeldActor()) return 1.f;
    return CarryIKAlpha(AnimInstance);
}
FVector UCarryInputLibrary::CarryLeftGripInRightHandSpace(UAnimInstance* AnimInstance)
{
    if(!AnimInstance||!AnimInstance->GetSkelMeshComponent()) return FVector::ZeroVector;
    const USkeletalMeshComponent* Mesh=AnimInstance->GetSkelMeshComponent();
    const UCarryComponent* Carry=Mesh->GetOwner()->FindComponentByClass<UCarryComponent>();
    if(!Carry) return FVector::ZeroVector;
    FTransform Reference=Mesh->GetSocketTransform(TEXT("hand_r"));
    if(Carry->State==ECarryState::Carrying||Carry->State==ECarryState::Aiming||Carry->GetFittedPickupAlpha()>0.f||Carry->GetFittedPlaceAlpha()>0.f) Reference.SetLocation(Carry->GetHandGrip(false).GetLocation());
    return Reference.InverseTransformPosition(Carry->GetHandGrip(true).GetLocation());
}

FTransform UCarryInputLibrary::CarryIKTarget(UAnimInstance* AnimInstance,bool bLeft)
{
    const AActor* Owner=AnimInstance?AnimInstance->GetOwningActor():nullptr;
    const UCarryComponent* Carry=Owner?Owner->FindComponentByClass<UCarryComponent>():nullptr;
    if(Carry&&Carry->GetFittedPlaceAlpha()>0.f) return FTransform(CarryGrip(AnimInstance,bLeft));
    return FTransform(bLeft?CarryLeftGripInRightHandSpace(AnimInstance):CarryGrip(AnimInstance,false));
}

float UCarryInputLibrary::CarryFootAlpha(UAnimInstance* AnimInstance)
{
    const AActor* A=AnimInstance?AnimInstance->GetOwningActor():nullptr;
    const UCarryComponent* C=A?A->FindComponentByClass<UCarryComponent>():nullptr;
    return C&&C->ShouldPlantCarryFeet()?1.f:0.f;
}
FTransform UCarryInputLibrary::CarryFootTarget(UAnimInstance* AnimInstance,bool bLeft)
{
    const AActor* A=AnimInstance?AnimInstance->GetOwningActor():nullptr;
    const UCarryComponent* C=A?A->FindComponentByClass<UCarryComponent>():nullptr;
    return C?C->GetCarryFootTarget(bLeft):FTransform::Identity;
}
