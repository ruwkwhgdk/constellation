#include "CarryComponent.h"
#include "CarryMath.h"
#include "HoldableComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/Controller.h"
#include "Components/CapsuleComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "GameFramework/PhysicsVolume.h"
#include "EngineUtils.h"
#include "PhysicsEngine/BodyInstance.h"
#include "PhysicsEngine/PhysicsSettings.h"

namespace
{
float PhysicsIntegrationStep(const UWorld* World)
{
    const UPhysicsSettings* Settings=UPhysicsSettings::Get();
    if(Settings->bTickPhysicsAsync) return Settings->AsyncFixedTimeStepSize;
    const float Frame=FMath::Min(World->GetDeltaSeconds(),Settings->MaxPhysicsDeltaTime);
    if(!Settings->bSubstepping) return Frame;
    const int32 Steps=FMath::Clamp(FMath::CeilToInt(Frame/Settings->MaxSubstepDeltaTime),1,Settings->MaxSubsteps);
    return FMath::Min(Frame/Steps,Settings->MaxSubstepDeltaTime);
}
bool UsesWorldGravity(UWorld* World,const FVector& Position)
{
    const APhysicsVolume* Volume=World->GetDefaultPhysicsVolume();
    for(TActorIterator<APhysicsVolume> It(World);It;++It)
        if(It->Priority>Volume->Priority&&It->EncompassesPoint(Position)) Volume=*It;
    return FMath::IsNearlyEqual(Volume->GetGravityZ(),World->GetGravityZ());
}
}

FTransform UCarryComponent::GetReleaseTransform() const
{
    FTransform Transform=ReleaseOffset*GetOwner()->GetActorTransform();
    if(HeldItem&&HeldItem->GetHoldMesh())
    {
        Transform.SetScale3D(HeldItem->GetHoldMesh()->GetComponentScale());
        const ACharacter* C=Cast<ACharacter>(GetOwner());
        const FBox Bounds=HeldItem->GetHoldMesh()->GetStaticMesh()->GetBoundingBox();
        const FVector Extent=Bounds.GetExtent()*HeldItem->GetHoldMesh()->GetComponentScale().GetAbs();
        const float MinForward=(C?C->GetCapsuleComponent()->GetScaledCapsuleRadius():35)+Extent.Size2D()+5;
        const FVector CenterOffset=Transform.GetRotation().RotateVector(Bounds.GetCenter()*Transform.GetScale3D());
        Transform.SetLocation(GetOwner()->GetActorLocation()+GetOwner()->GetActorForwardVector()*FMath::Max(ReleaseOffset.GetLocation().X,MinForward-FVector::DotProduct(CenterOffset,GetOwner()->GetActorForwardVector()))+FVector(0,0,ReleaseOffset.GetLocation().Z));
    }
    return Transform;
}
bool UCarryComponent::BeginAim()
{
    if(State!=ECarryState::Carrying || !IsValid(HeldItem) || !HeldItem->bCanThrow) return false;
    SetState(ECarryState::Aiming); PlayLoop(AimMontage); UpdateAim(); return true;
}
void UCarryComponent::CancelAim()
{
    if(State!=ECarryState::Aiming) return;
    ClearPreview(); bAimValid=false; SetState(ECarryState::Carrying); PlayLoop(HoldMontage);
}
void UCarryComponent::UpdateAim()
{
    bAimValid=false;
    if(State!=ECarryState::Aiming || !IsValid(HeldItem)) return;
    const ACharacter* C=Cast<ACharacter>(GetOwner());
    FVector View=C->GetPawnViewLocation(); FRotator ViewRotation=C->GetActorRotation();
    if(C->GetController()) C->GetController()->GetPlayerViewPoint(View,ViewRotation);
    const FVector Ray=ViewRotation.Vector(); const FTransform Release=GetReleaseTransform(); const FVector Start=Release.GetLocation();
    FCollisionQueryParams Params(SCENE_QUERY_STAT(CarryAim),false,GetOwner()); Params.AddIgnoredActor(GetHeldActor()); FHitResult Hit;
    const bool bHit=GetWorld()->LineTraceSingleByChannel(Hit,View,View+Ray*MaxThrowDistance,ECC_Visibility,Params);
    FVector Target=bHit?Hit.ImpactPoint:Start+Ray*MaxThrowDistance;
    if(!bHit)
    {
        FHitResult Ground;
        if(GetWorld()->LineTraceSingleByChannel(Ground,Target+FVector(0,0,200),Target-FVector(0,0,1600),ECC_Visibility,Params)) Target=Ground.ImpactPoint;
    }
    FVector Delta=Target-Start; const float Distance=Delta.Size();
    if(!FMath::IsFinite(Distance)||Distance<20) { ClearPreview(); return; }
    const float WeightRatio=FMath::Clamp(HeldItem->GetWeightKg()/FMath::Max(CharacterWeightKg*LiftWeightRatio,.01f),0.f,1.f);
    const float Range=MaxThrowDistance*FMath::Lerp(1.f,.7f,WeightRatio);
    if(Distance>Range) { Target=Start+Delta.GetSafeNormal()*Range; Delta=Target-Start; }
    ThrowTime=FMath::Lerp(MinFlightTime,MaxFlightTime,FMath::Clamp(Delta.Size()/MaxThrowDistance,0.f,1.f));
    CarryMath::Vector Velocity;
    if(!CarryMath::SolveThrow({Delta.X,Delta.Y,Delta.Z},GetWorld()->GetGravityZ(),ThrowTime,Velocity)) { ClearPreview(); return; }
    ThrowVelocity=FVector(Velocity.X,Velocity.Y,Velocity.Z); AimLocation=Target;
    const UStaticMeshComponent* Mesh=HeldItem->GetHoldMesh(); const FBox Box=Mesh->GetStaticMesh()->GetBoundingBox();
    const FVector Extent=Box.GetExtent()*Mesh->GetComponentScale().GetAbs();
    bAimValid=Mesh->BodyInstance.GravityGroupIndex==0&&UsesWorldGravity(GetWorld(),Start)&&IsSpaceFree(Release,true,true)&&IsPathFree(Mesh->GetComponentLocation(),Start,Release.GetRotation(),Hit);
    if(!bAimValid) UE_LOG(LogTemp,Verbose,TEXT("Carry aim launch blocked: held=%s release=%s COM=%s hit=%s normal=%s space=%d gravity=%d"),*Mesh->GetComponentLocation().ToString(),*Start.ToString(),*LocalCenterOfMass.ToString(),*GetNameSafe(Hit.GetActor()),*Hit.ImpactNormal.ToString(),IsSpaceFree(Release,true,true),Mesh->BodyInstance.GravityGroupIndex);
    FVector PreviousCenter=Release.TransformPosition(Box.GetCenter()); FQuat LandingRotation=Release.GetRotation();
    const FVector InitialCOMOffset=Release.GetRotation().RotateVector(LocalCenterOfMass*Release.GetScale3D());
    ThrowSpin=CarryMath::SpinDegreesPerSecond(Delta.Size(),MaxThrowDistance,ThrowTime);
    for(int32 Step=1;bAimValid&&Step<=100;++Step)
    {
        const float T=ThrowTime*Step/100.f;
        const FQuat Rot=FQuat(FVector::UpVector,FMath::DegreesToRadians(ThrowSpin*T))*Release.GetRotation();
        const FVector Position=Start+InitialCOMOffset+ThrowVelocity*T+FVector(0,0,.5f*GetWorld()->GetGravityZ()*T*T)-Rot.RotateVector(LocalCenterOfMass*Release.GetScale3D());
        if(!UsesWorldGravity(GetWorld(),Position)) { bAimValid=false; break; }
        const FVector Offset=Rot.RotateVector(Box.GetCenter()*Mesh->GetComponentScale());
        if(GetWorld()->SweepSingleByChannel(Hit,PreviousCenter,Position+Offset,Rot,Mesh->GetCollisionObjectType(),FCollisionShape::MakeBox(Extent+FVector(.5f)),Params,FCollisionResponseParams(Mesh->GetCollisionResponseToChannels())))
        {
            AimLocation=Hit.Location-Offset; LandingRotation=Rot;
            if(Step<=2||Hit.bStartPenetrating) { bAimValid=false; UE_LOG(LogTemp,Verbose,TEXT("Carry aim early hit step=%d actor=%s start=%s point=%s COM=%s"),Step,*GetNameSafe(Hit.GetActor()),*Start.ToString(),*Position.ToString(),*LocalCenterOfMass.ToString()); }
            break;
        }
        AimLocation=Position; PreviousCenter=Position+Offset; LandingRotation=Rot;
    }
    if(!PreviewMesh)
    {
        PreviewMesh=NewObject<UStaticMeshComponent>(GetOwner()); PreviewMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        PreviewMesh->SetCastShadow(false); PreviewMesh->SetStaticMesh(Mesh->GetStaticMesh()); PreviewMesh->RegisterComponent();
        if(PreviewMaterial) for(int32 Index=0;Index<PreviewMesh->GetNumMaterials();++Index)
        { PreviewMesh->SetMaterial(Index,PreviewMaterial); PreviewMesh->CreateAndSetMaterialInstanceDynamic(Index); }
    }
    PreviewMesh->SetWorldTransform(FTransform(LandingRotation,AimLocation,Mesh->GetComponentScale()));
    for(int32 Index=0;Index<PreviewMesh->GetNumMaterials();++Index)
        if(UMaterialInstanceDynamic* MID=Cast<UMaterialInstanceDynamic>(PreviewMesh->GetMaterial(Index)))
            MID->SetVectorParameterValue(TEXT("PreviewColor"),bAimValid?FLinearColor(0,.8f,.65f):FLinearColor(1,.1f,.1f));
}
bool UCarryComponent::CommitThrow()
{
    if(State!=ECarryState::Aiming) return false;
    UpdateAim();
    if(!bAimValid) { ShowFailure(GetCarryMessage(TEXT("ThrowBlocked"))); CancelAim(); return false; }
    ClearPreview(); AttachToActionHand(); bContactOccurred=false; SetState(ECarryState::Throwing); StartAction(ThrowMontage,ThrowContactTime,ThrowDuration,ThrowPlayRate); return true;
}
void UCarryComponent::OnThrowRelease()
{
    if(State!=ECarryState::Throwing||bContactOccurred||!IsValid(HeldItem)) return;
    const FTransform Release=GetReleaseTransform(); FHitResult Hit;
    if(!IsSpaceFree(Release,true,true)||!IsPathFree(HeldItem->GetHoldMesh()->GetComponentLocation(),Release.GetLocation(),Release.GetRotation(),Hit))
    { ShowFailure(GetCarryMessage(TEXT("ThrowBlocked"))); FinishAction(); return; }
    // Chaos advances with gravity first. Compensate its half-step bias at actual release,
    // so a frame-rate change during the wind-up does not use an outdated launch correction.
    FVector PhysicalVelocity=ThrowVelocity;
    PhysicalVelocity.Z-=.5f*GetWorld()->GetGravityZ()*PhysicsIntegrationStep(GetWorld());
    bContactOccurred=true; ReleaseHeld(Release,PhysicalVelocity,ThrowSpin);
}
