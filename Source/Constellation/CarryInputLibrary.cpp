#include "CarryInputLibrary.h"
#include "CarryComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/Controller.h"
#include "UObject/UnrealType.h"
#include "Animation/AnimInstance.h"
#include "Components/SkeletalMeshComponent.h"

bool UCarryInputLibrary::RouteCarryInput(AActor* Actor,FName Action,FName Phase)
{
    if(!IsValid(Actor)) return false;
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
    const FVector World=AnimInstance->GetOwningActor()->GetActorTransform().TransformPosition(FVector(0,bLeft?-30:30,10));
    return AnimInstance->GetSkelMeshComponent()->GetComponentTransform().InverseTransformPosition(World);
}
