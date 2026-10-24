#include "CarryComponent.h"
#include "HoldableComponent.h"
#include "GameFramework/Actor.h"
#include "CarryMath.h"
#include "CarryNoticeWidget.h"
#include "Internationalization/StringTable.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/CapsuleComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Engine/OverlapResult.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "TimerManager.h"
#include "Engine/LocalPlayer.h"
#include "Engine/GameViewportClient.h"
#include "UnrealClient.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

UCarryComponent::UCarryComponent() { PrimaryComponentTick.bCanEverTick = true; PrimaryComponentTick.TickGroup=TG_PostUpdateWork; }
const FHoldableItemRow* UCarryComponent::GetFittedProfile() const
{
    const FHoldableItemRow* Row=HeldItem?HeldItem->ItemRow.GetRow<FHoldableItemRow>(TEXT("Fitted carry")):nullptr;
    return Row&&Row->FittedThrowMontage&&Row->FittedHoldMontage?Row:nullptr;
}
void UCarryComponent::BeginPlay()
{
    Super::BeginPlay();
    if(const ACharacter* Character=Cast<ACharacter>(GetOwner())) AddTickPrerequisiteComponent(Character->GetMesh());
    ApplySettings(); GetOwner()->OnTakeAnyDamage.AddDynamic(this,&UCarryComponent::OnOwnerDamaged);
}
bool UCarryComponent::ApplySettings()
{
    if(State!=ECarryState::Idle) return false;
    if(!SettingsRow.DataTable) return true;
    const FCarrySettingsRow* Row=SettingsRow.GetRow<FCarrySettingsRow>(TEXT("Carry settings"));
    if(!Row) return false;
    CharacterWeightKg=Row->CharacterWeightKg;
    LiftWeightRatio=Row->LiftWeightRatio;
    Reach=Row->Reach;
    MaxThrowDistance=Row->MaxThrowDistance;
    MinFlightTime=Row->MinFlightTime;
    MaxFlightTime=Row->MaxFlightTime;
    CarrySocket=Row->CarrySocket;
    WeaponComponentName=Row->WeaponComponentName;
    ReleaseOffset=Row->ReleaseOffset;
    PickupMontage=Row->PickupMontage;
    PlaceMontage=Row->PlaceMontage;
    ThrowMontage=Row->ThrowMontage;
    HoldMontage=Row->HoldMontage;
    AimMontage=Row->AimMontage;
    PreviewMaterial=Row->PreviewMaterial;
    PickupActionSeconds=FMath::Clamp(FMath::IsFinite(Row->PickupActionSeconds)?Row->PickupActionSeconds:.75f,.5f,.9f);
    PlaceActionSeconds=FMath::Clamp(FMath::IsFinite(Row->PlaceActionSeconds)?Row->PlaceActionSeconds:.75f,.5f,.9f);
    ThrowActionSeconds=FMath::Clamp(FMath::IsFinite(Row->ThrowActionSeconds)?Row->ThrowActionSeconds:.75f,.5f,.9f);
    PickupPlayRate=Row->PickupPlayRate;
    PlacePlayRate=Row->PlacePlayRate;
    ThrowPlayRate=Row->ThrowPlayRate;
    PickupContactTime=Row->PickupContactTime;
    PickupDuration=Row->PickupDuration;
    PlaceContactTime=Row->PlaceContactTime;
    PlaceDuration=Row->PlaceDuration;
    ThrowContactTime=Row->ThrowContactTime;
    ThrowDuration=Row->ThrowDuration;
    NoticeDuration=Row->NoticeDuration;
    Messages=Row->Messages;
    CharacterWeightKg=FMath::Max(CharacterWeightKg,.01f); LiftWeightRatio=FMath::Max(LiftWeightRatio,0.f);
    Reach=FMath::Max(Reach,1.f); MaxThrowDistance=FMath::Max(MaxThrowDistance,1.f);
    MinFlightTime=FMath::Max(MinFlightTime,.01f); MaxFlightTime=FMath::Max(MaxFlightTime,MinFlightTime);
    PickupPlayRate=FMath::Max(PickupPlayRate,.01f); PlacePlayRate=FMath::Max(PlacePlayRate,.01f); ThrowPlayRate=FMath::Max(ThrowPlayRate,.01f);
    NoticeDuration=FMath::Max(NoticeDuration,.01f);
    return true;
}
FText UCarryComponent::GetCarryMessage(FName Key) const
{
    return Messages?FText::FromStringTable(Messages->GetStringTableId(),Key.ToString()):FText::GetEmpty();
}
void UCarryComponent::OnOwnerDamaged(AActor*,float Damage,const UDamageType*,AController*,AActor*) { if(Damage>0) AbortCarry(); }
void UCarryComponent::SetState(ECarryState Next) { State=Next; OnStateChanged.Broadcast(State); }
void UCarryComponent::ShowFailure(const FText& Message)
{
    OnMessage.Broadcast(Message);
    const ACharacter* C=Cast<ACharacter>(GetOwner()); APlayerController* PC=C?Cast<APlayerController>(C->GetController()):nullptr;
    if(!PC || !PC->IsLocalController()) return;
    if(!Notice) { Notice=CreateWidget<UCarryNoticeWidget>(PC); if(Notice) Notice->AddToViewport(50); }
    if(Notice) Notice->ShowMessage(Message,NoticeDuration);
}
bool UCarryComponent::CanReachItem(const UHoldableComponent* Item) const
{
    const UStaticMeshComponent* Mesh=Item?Item->GetHoldMesh():nullptr;
    if(!Mesh) return false;
    const FVector Start=GetOwner()->GetActorLocation();
    // A toppled floor-pivot prop can have its origin far beyond its visible body.
    if(Mesh->Bounds.GetBox().ComputeSquaredDistanceToPoint(Start)>FMath::Square(Reach)) return false;
    FCollisionQueryParams Params(SCENE_QUERY_STAT(CarryPickup),false,GetOwner());
    Params.AddIgnoredActor(Item->GetOwner()); FHitResult Hit;
    const bool bBlocked=GetWorld()->LineTraceSingleByChannel(Hit,Start,Mesh->Bounds.Origin,ECC_Visibility,Params);
    if(bBlocked) UE_LOG(LogTemp,Verbose,TEXT("Carry pickup sight blocked by %s.%s"),*GetNameSafe(Hit.GetActor()),*GetNameSafe(Hit.GetComponent()));
    return !bBlocked;
}
bool UCarryComponent::TryPickUp(UHoldableComponent* Item)
{
    ACharacter* C=Cast<ACharacter>(GetOwner());
    if(State!=ECarryState::Idle || !C || !IsValid(Item) || !Item->IsUsable() || Item->Carrier.IsValid()
        || Item->GetOwner()==C || !CanReachItem(Item)
        || C->GetCharacterMovement()->IsFalling()) return false;
    if(!CarryMath::CanLift(Item->GetWeightKg(),CharacterWeightKg,LiftWeightRatio))
    { ShowFailure(GetCarryMessage(TEXT("TooHeavy"))); return false; }
    bCarryFeetPlanted=false;
    Item->EndBallisticFlight(); HeldItem=Item; Item->Carrier=this; UStaticMeshComponent* Mesh=Item->GetHoldMesh();
    bSavedPhysics=Mesh->IsSimulatingPhysics(); bSavedGravity=Mesh->IsGravityEnabled(); SavedCollision=Mesh->GetCollisionEnabled();
    OriginalItemTransform=Mesh->GetComponentTransform(); bHasLifted=false;
    LocalCenterOfMass=Mesh->BodyInstance.IsValidBodyInstance()?OriginalItemTransform.InverseTransformPosition(Mesh->GetCenterOfMass()):Mesh->GetStaticMesh()->GetBoundingBox().GetCenter();
    TArray<USceneComponent*> Visuals; C->GetComponents(Visuals);
    for(USceneComponent* Visual:Visuals) if(Visual->GetFName()==WeaponComponentName)
    { WeaponVisual=Visual; bSavedWeaponVisible=Visual->IsVisible(); Visual->SetVisibility(false); break; }
    bContactOccurred=false; bPickupContactPending=false; SetState(ECarryState::PickingUp);
    if(const FHoldableItemRow* Row=GetFittedProfile(); Row&&Row->FittedPickupMontage)
    {
        PickupAlignStart=Mesh->GetComponentTransform();
        PickupAlignTarget=Row->FittedPickupMeshSpace*C->GetMesh()->GetComponentTransform();
        PickupAlignTarget.SetScale3D(PickupAlignStart.GetScale3D());
        // Pickup is already authorized by reach, visibility and weight. From here
        // the prop is non-colliding, including the approach to its authored pose.
        PickupAlignRoute={PickupAlignStart,PickupAlignTarget};
        PickupAlignDuration=PickupActionSeconds*.2f;
        C->GetCharacterMovement()->StopMovementImmediately(); CaptureCarryFeet();
        Mesh->SetSimulatePhysics(false); Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision); bPickupAlignmentTouched=true;
        bAligningPickup=true; PickupAlignElapsed=0; StartFittedPickup(); return true;
    }
    StartAction(PickupMontage,PickupContactTime,PickupDuration); return true;
}
void UCarryComponent::OnPickupContact()
{
    if(State!=ECarryState::PickingUp || bContactOccurred || !IsValid(HeldItem)) return;
    if(bAligningPickup) { bPickupContactPending=true; return; }
    bPickupContactPending=false;
    ACharacter* C=Cast<ACharacter>(GetOwner()); UStaticMeshComponent* Mesh=HeldItem->GetHoldMesh();
    if(!C || !Mesh) { AbortCarry(); return; }
    // Recheck reach/visibility at contact. Carrying is non-colliding: rotating
    // a toppled item into the carry pose must not require an empty upright box.
    if(!bPickupAlignmentTouched&&!CanReachItem(HeldItem))
    { ShowFailure(GetCarryMessage(TEXT("PickupUnreachable"))); AbortCarry(); return; }
    Mesh->SetSimulatePhysics(false); Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    const FName Hand=C->GetMesh()->DoesSocketExist(TEXT("hand_r"))?TEXT("hand_r"):TEXT("RightHand");
    if(GetFittedProfile())
    {
        PickupLiftStart=GetHeldActor()->GetActorTransform(); PickupLiftStartTime=GetWorld()->GetTimeSeconds();
        const UAnimInstance* Anim=C->GetMesh()->GetAnimInstance();
        PickupLiftSeconds=Anim&&ActiveMontage?FMath::Max(.1f,(ActiveMontage->GetPlayLength()-Anim->Montage_GetPosition(ActiveMontage))/FMath::Max(Anim->Montage_GetPlayRate(ActiveMontage),.01f)):.3f;
        GetHeldActor()->AttachToComponent(C->GetMesh(),FAttachmentTransformRules::KeepWorldTransform);
    }
    else if(C->GetMesh()->DoesSocketExist(Hand)) AttachToActionHand(); else AttachToCarryPosition();
    bContactOccurred=true; bHasLifted=true;
}
void UCarryComponent::AttachToCarryPosition()
{
    if(!IsValid(HeldItem)) return;
    ACharacter* C=Cast<ACharacter>(GetOwner()); const FVector Scale=HeldItem->GetHoldMesh()->GetComponentScale();
    if(GetFittedProfile())
    {
        GetHeldActor()->AttachToComponent(C->GetMesh(),FAttachmentTransformRules::KeepWorldTransform);
        GetHeldActor()->SetActorRelativeTransform(HeldItem->CarryOffset);
        GetHeldActor()->SetActorScale3D(Scale);
        return;
    }
    const bool bSocketExists=C->GetMesh()->DoesSocketExist(CarrySocket);
    GetHeldActor()->AttachToComponent(bSocketExists?static_cast<USceneComponent*>(C->GetMesh()):C->GetRootComponent(),FAttachmentTransformRules::KeepWorldTransform,bSocketExists?CarrySocket:NAME_None);
    GetHeldActor()->SetActorRelativeTransform(HeldItem->CarryOffset); GetHeldActor()->SetActorScale3D(Scale);
}
void UCarryComponent::AttachToActionHand()
{
    if(!IsValid(HeldItem)) return;
    ACharacter* C=Cast<ACharacter>(GetOwner()); const FName Hand=C->GetMesh()->DoesSocketExist(TEXT("hand_r"))?TEXT("hand_r"):TEXT("RightHand");
    if(GetFittedProfile()&&C->GetMesh()->DoesSocketExist(Hand))
    {
        FTransform Wrist=C->GetMesh()->GetSocketTransform(Hand); Wrist.SetScale3D(FVector::OneVector);
        FTransform Fitted=HeldItem->RightHandGrip.Inverse()*Wrist;
        Fitted.SetScale3D(HeldItem->GetHoldMesh()->GetComponentScale());
        GetHeldActor()->SetActorTransform(Fitted);
    }
    if(C->GetMesh()->DoesSocketExist(Hand)) GetHeldActor()->AttachToComponent(C->GetMesh(),FAttachmentTransformRules::KeepWorldTransform,Hand);
}
bool UCarryComponent::AllowsWalking() const { return State==ECarryState::Idle || State==ECarryState::Carrying || State==ECarryState::Aiming; }
AActor* UCarryComponent::GetHeldActor() const { return IsValid(HeldItem)?HeldItem->GetOwner():nullptr; }
FTransform UCarryComponent::GetHandGrip(bool bLeft) const
{
    if(bFittedPlacing&&State==ECarryState::Placing&&IsValid(HeldItem))
        return (bLeft?HeldItem->LeftHandGrip:HeldItem->RightHandGrip)*GetFittedPlaceTransform();
    if(GetFittedProfile()&&State==ECarryState::PickingUp&&bHasLifted)
        return (bLeft?HeldItem->LeftHandGrip:HeldItem->RightHandGrip)*GetFittedPickupTransform();
    if(GetFittedProfile()&&(State==ECarryState::Carrying||State==ECarryState::Aiming))
        if(const ACharacter* C=Cast<ACharacter>(GetOwner()))
            return (bLeft?HeldItem->LeftHandGrip:HeldItem->RightHandGrip)*HeldItem->CarryOffset*C->GetMesh()->GetComponentTransform();
    return IsValid(HeldItem)&&HeldItem->GetHoldMesh()?(bLeft?HeldItem->LeftHandGrip:HeldItem->RightHandGrip)*HeldItem->GetHoldMesh()->GetComponentTransform():FTransform::Identity;
}
bool UCarryComponent::IsSpaceFree(const FTransform& Transform,bool bIncludeCarrier,bool bLaunching) const
{
    if(!IsValid(HeldItem) || !HeldItem->GetHoldMesh()) return false;
    const UStaticMeshComponent* Mesh=HeldItem->GetHoldMesh(); const FBox Box=Mesh->GetStaticMesh()->GetBoundingBox();
    FCollisionQueryParams Params(SCENE_QUERY_STAT(CarrySpace),false,bIncludeCarrier?nullptr:GetOwner()); Params.AddIgnoredActor(GetHeldActor());
    // The owner's query-only animated mesh serves damage traces, not rigid-body contact.
    // Keep the physical capsule and every other actor in the launch clearance check.
    if(bLaunching) if(const ACharacter* Character=Cast<ACharacter>(GetOwner()))
        if(Character->GetMesh()->GetCollisionEnabled()==ECollisionEnabled::QueryOnly) Params.AddIgnoredComponent(Character->GetMesh());
    const FVector Extent=Box.GetExtent()*Mesh->GetComponentScale().GetAbs();
    const bool bFree=!GetWorld()->OverlapBlockingTestByChannel(Transform.TransformPosition(Box.GetCenter()),Transform.GetRotation(),Mesh->GetCollisionObjectType(),FCollisionShape::MakeBox(Extent.ComponentMax(FVector(1))),Params,FCollisionResponseParams(Mesh->GetCollisionResponseToChannels()));
    if(!bFree&&bIncludeCarrier&&UE_LOG_ACTIVE(LogTemp,Verbose))
    {
        TArray<FOverlapResult> Overlaps;
        GetWorld()->OverlapMultiByChannel(Overlaps,Transform.TransformPosition(Box.GetCenter()),Transform.GetRotation(),Mesh->GetCollisionObjectType(),FCollisionShape::MakeBox(Extent.ComponentMax(FVector(1))),Params,FCollisionResponseParams(Mesh->GetCollisionResponseToChannels()));
        for(const FOverlapResult& Overlap:Overlaps) if(Overlap.bBlockingHit) UE_LOG(LogTemp,Verbose,TEXT("Carry space blocker %s.%s"),*GetNameSafe(Overlap.GetActor()),*GetNameSafe(Overlap.GetComponent()));
    }
    return bFree;
}
bool UCarryComponent::IsPathFree(const FVector& Start,const FVector& End,const FQuat& Rotation,FHitResult& Hit) const
{
    if(!IsValid(HeldItem) || !HeldItem->GetHoldMesh()) return false;
    const UStaticMeshComponent* Mesh=HeldItem->GetHoldMesh(); const FBox Box=Mesh->GetStaticMesh()->GetBoundingBox();
    const FVector Offset=Rotation.RotateVector(Box.GetCenter()*Mesh->GetComponentScale()); const FVector Extent=Box.GetExtent()*Mesh->GetComponentScale().GetAbs();
    FCollisionQueryParams Params(SCENE_QUERY_STAT(CarryPath),false,GetOwner()); Params.AddIgnoredActor(GetHeldActor());
    const FCollisionShape Shape=FCollisionShape::MakeBox(Extent.ComponentMax(FVector(1)));
    const FCollisionResponseParams Response(Mesh->GetCollisionResponseToChannels());
    if(!GetWorld()->SweepSingleByChannel(Hit,Start+Offset,End+Offset,Rotation,Mesh->GetCollisionObjectType(),Shape,Params,Response)) return true;
    // Chaos can report a zero-time support hit without marking initial penetration.
    // Allow only initial floor contact (or shallow settling) while lifting away;
    // re-sweep from just above the support so walls/ceilings still block the lift.
    if(Hit.Time<=KINDA_SMALL_NUMBER&&(!Hit.bStartPenetrating||Hit.PenetrationDepth<2.f)
        &&Hit.ImpactNormal.Z>.75f&&FVector::DotProduct(End-Start,Hit.ImpactNormal)>0)
        return !GetWorld()->SweepSingleByChannel(Hit,Start+Offset+Hit.ImpactNormal*(Hit.PenetrationDepth+.5f),End+Offset,Rotation,Mesh->GetCollisionObjectType(),Shape,Params,Response);
    return false;
}
bool UCarryComponent::FindPlace(FTransform& Transform) const
{
    if(!IsValid(HeldItem)) return false;
    const FBox Box=HeldItem->GetHoldMesh()->GetStaticMesh()->GetBoundingBox(); const FVector Scale=HeldItem->GetHoldMesh()->GetComponentScale();
    const FVector Extent=Box.GetExtent()*Scale.GetAbs(); const ACharacter* C=Cast<ACharacter>(GetOwner());
    const float Radius=C?C->GetCapsuleComponent()->GetScaledCapsuleRadius():35;
    const FHoldableItemRow* Profile=GetFittedProfile();
    const bool bFitted=Profile&&Profile->FittedPlaceMontage&&C;
    const FTransform Authored=bFitted?Profile->FittedPlaceMeshSpace*C->GetMesh()->GetComponentTransform():FTransform::Identity;
    const FVector Center=bFitted?Authored.TransformPosition(Box.GetCenter()):GetOwner()->GetActorLocation()+GetOwner()->GetActorForwardVector()*(Radius+Extent.Size2D()+20);
    FCollisionQueryParams Params(SCENE_QUERY_STAT(CarryFloor),false,GetOwner()); Params.AddIgnoredActor(GetHeldActor()); FHitResult Floor;
    const UStaticMeshComponent* Mesh=HeldItem->GetHoldMesh();
    if(!GetWorld()->LineTraceSingleByChannel(Floor,Center+FVector(0,0,50),Center-FVector(0,0,200),Mesh->GetCollisionObjectType(),Params,FCollisionResponseParams(Mesh->GetCollisionResponseToChannels())) || Floor.ImpactNormal.Z<.75f) return false;
    const FQuat Rot=bFitted?Authored.GetRotation():(FRotator(0,GetOwner()->GetActorRotation().Yaw,0)+HeldItem->PlaceRotation).Quaternion();
    const float Support=FMath::Abs(Rot.GetAxisX().Z)*Extent.X+FMath::Abs(Rot.GetAxisY().Z)*Extent.Y+FMath::Abs(Rot.GetAxisZ().Z)*Extent.Z;
    Transform=FTransform(Rot,Floor.ImpactPoint+FVector(0,0,Support+(bFitted?.1f:3.f))-Rot.RotateVector(Box.GetCenter()*Scale),Scale);
    FHitResult Hit; const bool bFree=IsSpaceFree(Transform);
    const bool bPath=IsPathFree(HeldItem->GetHoldMesh()->GetComponentLocation(),Transform.GetLocation(),Rot,Hit);
    if(!bFree||!bPath) UE_LOG(LogTemp,Verbose,TEXT("Carry place blocked: free=%d path=%d start=%s target=%s hit=%s depth=%f normal=%s"),bFree,bPath,*HeldItem->GetHoldMesh()->GetComponentLocation().ToString(),*Transform.GetLocation().ToString(),*GetNameSafe(Hit.GetActor()),Hit.PenetrationDepth,*Hit.ImpactNormal.ToString());
    return bFree&&bPath;
}
bool UCarryComponent::TryPlace()
{
    if(State!=ECarryState::Carrying) return false;
    if(!FindPlace(PlaceTransform)) { ShowFailure(GetCarryMessage(TEXT("PlaceBlocked"))); return false; }
    const FHoldableItemRow* Row=GetFittedProfile();
    bFittedPlacing=Row&&Row->FittedPlaceMontage;
    bPlaceReleasePending=false;
    if(bFittedPlacing)
    {
        PlaceStartTransform=HeldItem->GetHoldMesh()->GetComponentTransform();
        GetHeldActor()->DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);
        PlaceStartTime=GetWorld()->GetTimeSeconds(); CaptureCarryFeet();
    }
    else AttachToActionHand();
    bContactOccurred=false; SetState(ECarryState::Placing);
    StartAction(bFittedPlacing?Row->FittedPlaceMontage.Get():PlaceMontage.Get(),bFittedPlacing?3.4f:PlaceContactTime,bFittedPlacing?6.f:PlaceDuration); return true;
}
void UCarryComponent::OnPlaceRelease()
{
    if(State!=ECarryState::Placing || bContactOccurred) return;
    if(bFittedPlacing) { bPlaceReleasePending=true; return; }
    FTransform Current;
    if(!FindPlace(Current)||!Current.GetLocation().Equals(PlaceTransform.GetLocation(),5.f)||!IsSpaceFree(PlaceTransform))
    { ShowFailure(GetCarryMessage(TEXT("PlaceBlocked"))); FinishAction(); return; }
    bContactOccurred=true; ReleaseHeld(PlaceTransform,FVector::ZeroVector,0);
}
void UCarryComponent::ReleaseHeld(const FTransform& Transform,const FVector& Velocity,float Spin)
{
    if(!IsValid(HeldItem)) return;
    UStaticMeshComponent* Mesh=HeldItem->GetHoldMesh(); AActor* Actor=GetHeldActor();
    Actor->DetachFromActor(FDetachmentTransformRules::KeepWorldTransform); Actor->SetActorTransform(Transform);
    Mesh->SetCollisionEnabled(SavedCollision);
    // Carry throws use free ballistic flight, matching the landing preview.
    if(State==ECarryState::Throwing) HeldItem->BeginBallisticFlight();
    Mesh->SetEnableGravity(true); Mesh->SetSimulatePhysics(true);
    Mesh->SetPhysicsLinearVelocity(Velocity); Mesh->SetPhysicsAngularVelocityInDegrees(FVector(0,0,Spin));
    HeldItem->Carrier.Reset(); HeldItem=nullptr;
}
void UCarryComponent::PlayLoop(UAnimMontage* Montage)
{
    if(const FHoldableItemRow* Row=GetFittedProfile()) Montage=Row->FittedHoldMontage;
    ACharacter* C=Cast<ACharacter>(GetOwner()); UAnimInstance* Anim=C?C->GetMesh()->GetAnimInstance():nullptr;
    if(Anim&&Montage)
    {
        const FHoldableItemRow* Row=GetFittedProfile();
        const bool bMatchedPickup=Row&&ActiveMontage==Row->FittedPickupMontage;
        ActiveMontage=Montage;
        // Pickup ends at the hold pose. Blending two different slots would
        // briefly mix idle into both slots and lose the furniture contact.
        if(bMatchedPickup) Anim->Montage_PlayWithBlendIn(Montage,FAlphaBlendArgs(0.f));
        else Anim->Montage_Play(Montage);
        if(Montage->GetNumSections()>0) Anim->Montage_SetNextSection(Montage->GetSectionName(0),Montage->GetSectionName(0),Montage);
    }
}
void UCarryComponent::StartAction(UAnimMontage* Montage,float ContactTime,float Duration)
{
    ACharacter* C=Cast<ACharacter>(GetOwner()); if(C) C->GetCharacterMovement()->StopMovementImmediately();
    GetWorld()->GetTimerManager().ClearTimer(ContactTimer); GetWorld()->GetTimerManager().ClearTimer(FinishTimer);
    bActionFinishPending=false;
    const float Seconds=FMath::Clamp(State==ECarryState::PickingUp?PickupActionSeconds:State==ECarryState::Placing?PlaceActionSeconds:ThrowActionSeconds,.5f,.9f);
    // Finish after the mesh/notify update, including a delayed release on this frame.
    GetWorld()->GetTimerManager().SetTimer(FinishTimer,FTimerDelegate::CreateWeakLambda(this,[this]() { bActionFinishPending=true; }),Seconds,false);
    UAnimInstance* Anim=C?C->GetMesh()->GetAnimInstance():nullptr;
    const float PlayRate=Montage?Montage->GetPlayLength()/(Seconds*FMath::Max(Montage->RateScale,.01f)):1.f;
    if(Anim&&Montage&&Anim->Montage_Play(Montage,PlayRate)>0)
    {
        ActiveMontage=Montage; FOnMontageEnded Delegate; Delegate.BindUObject(this,&UCarryComponent::OnMontageFinished); Anim->Montage_SetEndDelegate(Delegate,Montage); return;
    }
    // Preserve the source contact proportion when no animation instance is available.
    GetWorld()->GetTimerManager().SetTimer(ContactTimer,FTimerDelegate::CreateWeakLambda(this,[this]()
    { if(State==ECarryState::PickingUp) OnPickupContact(); else if(State==ECarryState::Placing) OnPlaceRelease(); else if(State==ECarryState::Throwing) OnThrowRelease(); }),Seconds*FMath::Clamp(ContactTime/FMath::Max(Duration,.01f),.01f,.95f),false);
}
void UCarryComponent::OnMontageFinished(UAnimMontage* Montage,bool bInterrupted)
{
    if(Montage!=ActiveMontage || bAborting) return;
    if(bInterrupted) AbortCarry(); else bActionFinishPending=true;
}
void UCarryComponent::FinishAction()
{
    bFittedPlacing=false; bPlaceReleasePending=false;
    bActionFinishPending=false;
    GetWorld()->GetTimerManager().ClearTimer(ContactTimer); GetWorld()->GetTimerManager().ClearTimer(FinishTimer);
    if(State!=ECarryState::PickingUp && State!=ECarryState::Placing && State!=ECarryState::Throwing) return;
    if(IsValid(HeldItem)&&(State!=ECarryState::PickingUp || bContactOccurred)) { AttachToCarryPosition(); SetState(ECarryState::Carrying); PlayLoop(HoldMontage); }
    else AbortCarry();
}
void UCarryComponent::ClearPreview() { if(PreviewMesh) { PreviewMesh->DestroyComponent(); PreviewMesh=nullptr; } }
void UCarryComponent::AbortCarry()
{
    if(bAborting) return; bAborting=true; bActionFinishPending=false; bFittedReleasePending=false; bAligningPickup=false; bPickupContactPending=false; bFittedPlacing=false; bPlaceReleasePending=false;
    GetWorld()->GetTimerManager().ClearTimer(ContactTimer); GetWorld()->GetTimerManager().ClearTimer(FinishTimer); ClearPreview(); bAimValid=false;
    ACharacter* C=Cast<ACharacter>(GetOwner());
    if(C&&ActiveMontage&&C->GetMesh()->GetAnimInstance()) C->GetMesh()->GetAnimInstance()->Montage_Stop(.1f,ActiveMontage);
    ActiveMontage=nullptr;
    if(IsValid(HeldItem))
    {
        if(UStaticMeshComponent* Mesh=HeldItem->GetHoldMesh())
        {
            if(bHasLifted)
            {
                FTransform Drop=GetReleaseTransform(); bool bSafe=IsSpaceFree(Drop,true);
                for(int32 I=0;!bSafe&&I<24;++I)
                {
                    const float Angle=I*PI/12.f; const float Radius=100+Mesh->Bounds.BoxExtent.Size2D();
                    Drop.SetLocation(GetOwner()->GetActorLocation()+FVector(FMath::Cos(Angle)*Radius,FMath::Sin(Angle)*Radius,30));
                    bSafe=IsSpaceFree(Drop,true);
                }
                if(!bSafe) { Drop=OriginalItemTransform; bSafe=IsSpaceFree(Drop,true); }
                GetHeldActor()->DetachFromActor(FDetachmentTransformRules::KeepWorldTransform); GetHeldActor()->SetActorTransform(Drop);
                HeldItem->RestoreWhenClear(SavedCollision,bSavedGravity,bSavedPhysics);
            }
            else if(bPickupAlignmentTouched)
            {
                if(bSavedPhysics) HeldItem->RestoreWhenClear(SavedCollision,bSavedGravity,true);
                else { Mesh->SetCollisionEnabled(SavedCollision); Mesh->SetEnableGravity(bSavedGravity); }
            }
            // Legacy precontact items retain their original attachment and simulation.
        }
        HeldItem->Carrier.Reset();
    }
    HeldItem=nullptr; bPickupAlignmentTouched=false;
    if(WeaponVisual.IsValid()) WeaponVisual->SetVisibility(bSavedWeaponVisible);
    WeaponVisual.Reset();
    bContactOccurred=false; SetState(ECarryState::Idle); bAborting=false;
}
bool UCarryComponent::HandleInteract()
{
    if(State==ECarryState::Aiming) { CancelAim(); return true; }
    if(State==ECarryState::Carrying) { TryPlace(); return true; }
    if(State!=ECarryState::Idle) return true;
    if(UHoldableComponent* Item=FindInteractionItem()) { TryPickUp(Item); return true; }
    return false;
}
UHoldableComponent* UCarryComponent::FindInteractionItem() const
{
    FHitResult Hit; FCollisionQueryParams Params(SCENE_QUERY_STAT(CarryInteract),false,GetOwner()); const FVector Start=GetOwner()->GetActorLocation();
    if(GetWorld()->SweepSingleByChannel(Hit,Start,Start+GetOwner()->GetActorForwardVector()*Reach-FVector(0,0,65),FQuat::Identity,ECC_Visibility,FCollisionShape::MakeSphere(35),Params))
        if(Hit.GetActor())
        {
            UE_LOG(LogTemp,Verbose,TEXT("Carry selection hit %s.%s"),*GetNameSafe(Hit.GetActor()),*GetNameSafe(Hit.GetComponent()));
            return Hit.GetActor()->FindComponentByClass<UHoldableComponent>();
        }
    return nullptr;
}
bool UCarryComponent::CanPickUp(const UHoldableComponent* Item) const
{
    const ACharacter* C=Cast<ACharacter>(GetOwner());
    return State==ECarryState::Idle && C && IsValid(Item) && Item->IsUsable() && !Item->Carrier.IsValid()
        && Item->GetOwner()!=C && CanReachItem(Item) && !C->GetCharacterMovement()->IsFalling()
        && CarryMath::CanLift(Item->GetWeightKg(),CharacterWeightKg,LiftWeightRatio);
}
bool UCarryComponent::CanPlace() const
{
    FTransform Transform;
    return State==ECarryState::Carrying && FindPlace(Transform);
}
void UCarryComponent::TickComponent(float Dt,ELevelTick Type,FActorComponentTickFunction* Fn)
{
    Super::TickComponent(Dt,Type,Fn);
    if(bFittedPlacing&&State==ECarryState::Placing) UpdateFittedPlace();
    if(bCarryFeetPlanted&&GetOwner()->GetVelocity().SizeSquared()>9.f) bCarryFeetPlanted=false;
    if(GetFittedProfile()&&State==ECarryState::PickingUp&&bHasLifted) GetHeldActor()->SetActorTransform(GetFittedPickupTransform());
    if(bFittedReleasePending) { bFittedReleasePending=false; PerformThrowRelease(); }
    if(State==ECarryState::Idle) return;
    if(!IsValid(HeldItem)&&State!=ECarryState::Placing&&State!=ECarryState::Throwing) { AbortCarry(); return; }
    ACharacter* C=Cast<ACharacter>(GetOwner()); APlayerController* PC=C?Cast<APlayerController>(C->GetController()):nullptr;
    if(PC&&PC->IsMoveInputIgnored()) { AbortCarry(); return; }
    // Fitted pickup holds its final pose until this handoff; never blend via idle.
    if(State==ECarryState::PickingUp&&bContactOccurred&&!bAligningPickup)
    {
        const FHoldableItemRow* Row=GetFittedProfile(); UAnimInstance* Anim=C?C->GetMesh()->GetAnimInstance():nullptr;
        if(Row&&ActiveMontage==Row->FittedPickupMontage&&Anim&&Anim->Montage_GetPosition(ActiveMontage)>=ActiveMontage->GetPlayLength()-.002f)
            FinishAction();
    }
    if(bAligningPickup)
    {
        PickupAlignElapsed+=Dt; const float T=FMath::Clamp(PickupAlignElapsed/PickupAlignDuration,0.f,1.f);
        const float RouteT=T*(PickupAlignRoute.Num()-1); const int32 Segment=FMath::Min(FMath::FloorToInt(RouteT),PickupAlignRoute.Num()-2);
        const float Blend=FMath::Clamp(RouteT-Segment,0.f,1.f);
        FTransform Next; Next.Blend(PickupAlignRoute[Segment],PickupAlignRoute[Segment+1],Blend*Blend*(3.f-2.f*Blend));
        HeldItem->GetHoldMesh()->SetWorldTransform(Next);
        if(T>=1.f) { bAligningPickup=false; if(bPickupContactPending) OnPickupContact(); }
    }
    if(bActionFinishPending) FinishAction();
    if(State==ECarryState::Aiming&&PC&&!FParse::Param(FCommandLine::Get(),TEXT("RenderOffscreen")))
    {
        const ULocalPlayer* Player=PC->GetLocalPlayer();
        if(Player&&Player->ViewportClient&&Player->ViewportClient->Viewport&&!Player->ViewportClient->Viewport->HasFocus()) { CancelAim(); return; }
    }
    if(State==ECarryState::Aiming&&PC) { FRotator Rot=GetOwner()->GetActorRotation(); Rot.Yaw=PC->GetControlRotation().Yaw; GetOwner()->SetActorRotation(Rot); }
    if(State==ECarryState::Aiming)
    {
        UpdateAim();
    }
}
void UCarryComponent::EndPlay(const EEndPlayReason::Type Reason)
{
    AbortCarry(); if(Notice) { Notice->RemoveFromParent(); Notice=nullptr; } Super::EndPlay(Reason);
}

bool UCarryComponent::AllowsCombatAction_Implementation(FString& Reason) const
{
    if(BlocksOtherActions()){Reason=TEXT("Carry interaction active");return false;}
    Reason.Reset();return true;
}

FTransform UCarryComponent::GetFittedPickupTransform() const
{
    const ACharacter* C=CastChecked<ACharacter>(GetOwner());
    FTransform Target=HeldItem->CarryOffset*C->GetMesh()->GetComponentTransform();
    Target.SetScale3D(PickupLiftStart.GetScale3D());
    const float T=FMath::Clamp((GetWorld()->GetTimeSeconds()-PickupLiftStartTime)/PickupLiftSeconds,0.f,1.f);
    FTransform Result; Result.Blend(PickupLiftStart,Target,T*T*(3.f-2.f*T)); return Result;
}
float UCarryComponent::GetFittedPickupAlpha() const
{
    if(State!=ECarryState::PickingUp||bAligningPickup) return 0.f;
    const FHoldableItemRow* Row=GetFittedProfile();
    if(Row&&Row->FittedPickupMontage)
    {
        if(bHasLifted) return 1.f;
        const ACharacter* C=Cast<ACharacter>(GetOwner()); const UAnimInstance* Anim=C?C->GetMesh()->GetAnimInstance():nullptr;
        return Anim&&ActiveMontage?FMath::Clamp((Anim->Montage_GetPosition(ActiveMontage)-.75f)/.25f,0.f,1.f):0.f;
    }
    return Row&&bHasLifted?FMath::Clamp((GetWorld()->GetTimeSeconds()-PickupLiftStartTime)/.10f,0.f,1.f):0.f;
}
void UCarryComponent::CaptureCarryFeet()
{
    if(const ACharacter* C=Cast<ACharacter>(GetOwner()))
    { CarryFootWorld[0]=C->GetMesh()->GetSocketTransform(TEXT("foot_l")); CarryFootWorld[1]=C->GetMesh()->GetSocketTransform(TEXT("foot_r")); bCarryFeetPlanted=true; }
}
bool UCarryComponent::ShouldPlantCarryFeet() const
{
    const ACharacter* C=Cast<ACharacter>(GetOwner());
    return bCarryFeetPlanted&&C&&FVector::DistSquared(CarryFootWorld[0].GetLocation(),C->GetMesh()->GetSocketLocation(TEXT("foot_l")))<FMath::Square(30.f)&&C->GetVelocity().SizeSquared()<9.f&&!C->GetCharacterMovement()->IsFalling()&&(State==ECarryState::Throwing||State==ECarryState::Idle||State==ECarryState::Carrying||State==ECarryState::PickingUp||State==ECarryState::Placing);
}
FTransform UCarryComponent::GetCarryFootTarget(bool bLeft) const
{
    const ACharacter* C=CastChecked<ACharacter>(GetOwner());
    return CarryFootWorld[bLeft?0:1].GetRelativeTransform(C->GetMesh()->GetComponentTransform());
}

void UCarryComponent::StartFittedPickup()
{
    const FHoldableItemRow* Row=GetFittedProfile();
    if(!Row||!Row->FittedPickupMontage) { AbortCarry(); return; }
    StartAction(Row->FittedPickupMontage,1.f,2.5f);
}
