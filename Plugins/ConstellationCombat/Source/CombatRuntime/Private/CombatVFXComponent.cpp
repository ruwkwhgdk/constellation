#include "CombatVFXComponent.h"
#include "CombatSurfaceContact.h"
#include "CombatAbilitySystem.h"
#include "CombatLabCharacter.h"
#include "ConstellationFXLibrary.h"
#include "ConstellationFXActor.h"
#include "NiagaraComponent.h"
#include "NiagaraFunctionLibrary.h"
#include "TimerManager.h"
#include "ConstellationSwordRibbonComponent.h"
#include "NiagaraSystem.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Engine/SkeletalMesh.h"
#include "PhysicalMaterials/PhysicalMaterial.h"
#include "Misc/App.h"
#include "Camera/PlayerCameraManager.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

UCombatVFXComponent::UCombatVFXComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    // SwordTrail remains serialized for compatibility; the shared ribbon is the active trail.
}
void UCombatVFXComponent::Initialize(UCombatAbilitySystem* System)
{
    if (Combat.Get()==System) return;
    if (auto* Previous=Combat.Get())
    {
        Previous->OnHitConfirmed.RemoveAll(this);
        Previous->OnHitWindowOpened.RemoveAll(this);
        Previous->OnHitWindowClosed.RemoveAll(this);
        Previous->OnDied.RemoveAll(this);
        Previous->OnHitReceived.RemoveAll(this);
        Previous->OnDodgeStarted.RemoveAll(this);
    }
    StopPresentation(); Combat=System;
    if (System) PrepareReviewWeapon();
    if (!System) return;
    System->OnHitConfirmed.AddUObject(this,&UCombatVFXComponent::ConfirmedHit);
    System->OnHitWindowOpened.AddUObject(this,&UCombatVFXComponent::OpenWindow);
    System->OnHitWindowClosed.AddUObject(this,&UCombatVFXComponent::CloseWindow);
    System->OnDied.AddUObject(this,&UCombatVFXComponent::StopPresentation);
    System->OnHitReceived.AddUObject(this,&UCombatVFXComponent::StopPresentation);
    System->OnDodgeStarted.AddUObject(this,&UCombatVFXComponent::StopAttackPresentation);
}
void UCombatVFXComponent::SetPresentationEnabled(bool Enabled)
{
    bPresentationEnabled=Enabled;
    if (!Enabled) StopPresentation();
    else PrepareReviewWeapon();
}
ECombatVFXStyle UCombatVFXComponent::ResolveStyle() const
{
    if (Style!=ECombatVFXStyle::Auto) return Style;
    const auto* Character=Cast<ACharacter>(GetOwner());
    const auto* Mesh=Character?Character->GetMesh()->GetSkeletalMeshAsset():nullptr;
    return Mesh && Mesh->GetName().Contains(TEXT("Slime")) ? ECombatVFXStyle::Slime : ECombatVFXStyle::Sword;
}
void UCombatVFXComponent::PrepareReviewWeapon()
{
    auto* Character=Cast<ACombatLabCharacter>(GetOwner());
    if (!bPresentationEnabled) return;
    // Retain shared rendering assets from opt-in initialization, before the first short impact window.
    if (PresentationAssets.IsEmpty())
        for (const TCHAR* Path : {TEXT("/Engine/BasicShapes/Sphere.Sphere"),TEXT("/Engine/BasicShapes/Plane.Plane"),TEXT("/Engine/BasicShapes/Cylinder.Cylinder"),
            TEXT("/Game/Constellation/VFX/Materials/M_FX_Glow.M_FX_Glow"),TEXT("/Game/Constellation/VFX/Materials/M_FX_Gel.M_FX_Gel"),
            TEXT("/Game/Constellation/VFX/Materials/M_FX_Impact.M_FX_Impact"),TEXT("/Game/Constellation/VFX/Materials/M_FX_GelImpact.M_FX_GelImpact"),
            TEXT("/Game/Constellation/VFX/Materials/M_FX_Cut.M_FX_Cut"),TEXT("/Game/Constellation/VFX/Materials/M_FX_ImpactStar.M_FX_ImpactStar"),
            TEXT("/Game/Constellation/VFX/Materials/M_FX_Slash.M_FX_Slash"),TEXT("/Game/Constellation/VFX/Materials/M_FX_Soft.M_FX_Soft"),TEXT("/Game/Constellation/VFX/Materials/M_FX_Dust.M_FX_Dust"),TEXT("/Game/Constellation/VFX/Materials/M_FX_Ring.M_FX_Ring")})
            if (auto* Asset=LoadObject<UObject>(nullptr,Path)) PresentationAssets.Add(Asset);
    WarmupRendering();
    // The ribbon material is retained before its short hit window.
    if (ResolveStyle()!=ECombatVFXStyle::Sword) return;
    if (!Character || !Character->Sword || Character->Sword->GetStaticMesh()) return;
    auto* Mesh=Character->GetMesh();
    if (!Mesh->GetSkeletalMeshAsset()) return;
    auto* SwordMesh=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/Constellation/Characters/Shared/Equipment/SM_Weapon_Sword.SM_Weapon_Sword"));
    if (!SwordMesh) return;
    if (Mesh->DoesSocketExist(TEXT("WeaponSocket")))
    {
        Character->Sword->AttachToComponent(Mesh,FAttachmentTransformRules::SnapToTargetNotIncludingScale,TEXT("WeaponSocket"));
        Character->Sword->SetRelativeScale3D(FVector::OneVector);
        Character->Sword->SetStaticMesh(SwordMesh);return;
    }
    // Only the maintained refined preview lacks the production socket. Reconstruct its vetted
    // Attack01/polish_attack.py grip from mapped finger bones; do not alter its rig or animation.
    if (Mesh->GetSkeletalMeshAsset()->GetName()!=TEXT("SK_player_heroine_new_RunPreview")) return;
    for (FName Bone : {FName("hand_r"),FName("middle_01_r"),FName("index_01_r"),FName("pinky_01_r"),FName("middle_02_r"),FName("ring_02_r")})
        if (Mesh->GetBoneIndex(Bone)==INDEX_NONE) return;
    Mesh->RefreshBoneTransforms();
    const FVector Across=(Mesh->GetBoneLocation(TEXT("index_01_r"))-Mesh->GetBoneLocation(TEXT("pinky_01_r"))).GetSafeNormal();
    const FVector Length=(Mesh->GetBoneLocation(TEXT("middle_01_r"))-Mesh->GetBoneLocation(TEXT("hand_r"))).GetSafeNormal();
    if (Across.IsNearlyZero() || Length.IsNearlyZero()) return;
    const FQuat Rotation=FRotationMatrix::MakeFromXZ(Length,-Across).ToQuat();
    const FVector PalmNormal=FVector::CrossProduct(Length,Across).GetSafeNormal();
    const FVector Grip=(Mesh->GetBoneLocation(TEXT("middle_02_r"))+Mesh->GetBoneLocation(TEXT("ring_02_r")))*.5f-PalmNormal;
    const FVector Origin=Grip-Rotation.RotateVector(FVector(0,0,65.f))*.5f;
    Character->Sword->SetStaticMesh(SwordMesh);
    Character->Sword->AttachToComponent(Mesh,FAttachmentTransformRules::KeepWorldTransform,TEXT("hand_r"));
    Character->Sword->SetWorldTransform(FTransform(Rotation,Origin,FVector(.5f)));
}
void UCombatVFXComponent::WarmupRendering()
{
    UWorld* World=GetWorld();
    if(bRenderingWarmupDone || !Combat.IsValid() || !World || !World->IsGameWorld() || !World->GetGameInstance() ||
        World->GetNetMode()==NM_DedicatedServer || IsRunningCommandlet() || !FApp::CanEverRender() || !IsValid(GetOwner())) return;
    bRenderingWarmupDone=true;
    const FVector HiddenLocation=GetOwner()->GetActorLocation()-FVector(0,0,100000);
    auto Prepare=[&](EConstellationFXKind Kind,FLinearColor Color,float Scale)
    {
        if(auto* Effect=UConstellationFXLibrary::SpawnEffect(this,Kind,HiddenLocation,FVector::UpVector,Color,Scale))
        {
            // Register the actual ISM/material permutations without combat, visibility or persistent scene actors.
            Effect->Tags.Add(TEXT("CombatVFXWarmup"));Effect->SetOwner(GetOwner());Effect->SetLifeSpan(1.1f);
            WarmupEffects.Add(Effect);
        }
    };
    Prepare(EConstellationFXKind::SwordHit,SwordColor,UConstellationFXLibrary::CombatScale(EConstellationFXKind::SwordHit));
    Prepare(EConstellationFXKind::SlimeHit,SlimeColor,UConstellationFXLibrary::CombatScale(EConstellationFXKind::SlimeHit));
    Prepare(EConstellationFXKind::PlayerHit,UConstellationFXLibrary::CombatColor(EConstellationFXKind::PlayerHit),UConstellationFXLibrary::CombatScale(EConstellationFXKind::PlayerHit));
    Prepare(EConstellationFXKind::RunDust,FLinearColor(.34f,.25f,.17f,.45f),.8f);
}
USceneComponent* UCombatVFXComponent::ResolveWeapon()
{
    if (Weapon.IsValid()) return Weapon.Get();
    if (!GetOwner()) return nullptr;
    TInlineComponentArray<USceneComponent*> Components(GetOwner());
    for (auto* Component : Components)
        if ((Component->GetFName()==WeaponComponentName || Component->ComponentHasTag(TEXT("CombatWeapon"))) &&
            (!Cast<UStaticMeshComponent>(Component) || Cast<UStaticMeshComponent>(Component)->GetStaticMesh()))
        { Weapon=Component; return Component; }
    return nullptr;
}
void UCombatVFXComponent::OpenWindow(uint64 Id,FName Window)
{
    if (!bPresentationEnabled || !IsValid(GetOwner()) || !Combat.IsValid() || Combat->GetHealth()<=0 || GetWorld()->GetNetMode()==NM_DedicatedServer) return;
    if (Execution!=Id) { StopAttackPresentation(); Execution=Id; }
    const bool WasEmpty=OpenWindows.IsEmpty(); OpenWindows.Add(Window);
    if (!WasEmpty) return;
    if (SpawnCue(AttackCue,GetOwner()->GetActorLocation()+GetOwner()->GetActorForwardVector()*35.f,GetOwner()->GetActorForwardVector(),true)) return;
    if (ResolveStyle()==ECombatVFXStyle::Slime)
    {
        auto* Effect=UConstellationFXLibrary::SpawnEffect(this,EConstellationFXKind::SlimeAttack,
            GetOwner()->GetActorLocation()+GetOwner()->GetActorForwardVector()*35.f,GetOwner()->GetActorForwardVector(),SlimeColor,UConstellationFXLibrary::CombatScale(EConstellationFXKind::SlimeAttack));
        if (Effect) { Effect->SetOwner(GetOwner()); Effect->AttachToActor(GetOwner(),FAttachmentTransformRules::KeepWorldTransform); SlimeAttack=Effect; }
    }
    else if (auto* Attachment=ResolveWeapon())
    {
        WeaponRibbon=NewObject<UConstellationSwordRibbonComponent>(GetOwner());
        WeaponRibbon->SetupAttachment(GetOwner()->GetRootComponent());
        WeaponRibbon->Configure(SwordColor);
        WeaponRibbon->RegisterComponent();
        PreviousTip=Attachment->GetComponentTransform().TransformPosition(FVector(0,0,-95));
        bPreviousTipValid=true;
        WeaponRibbon->AddTip(PreviousTip,0.f);
    }
}
void UCombatVFXComponent::CloseWindow(uint64 Id,FName Window)
{
    if (Execution!=Id) return;
    OpenWindows.Remove(Window);
    if (OpenWindows.IsEmpty()) StopAttackPresentation();
}
void UCombatVFXComponent::ConfirmedHit(const FCombatConfirmedHit& Hit)
{
    if (!IsValid(GetOwner()) || !Combat.IsValid() || Combat->GetHealth()<=0 || Hit.Source.Get()!=GetOwner() || GetWorld()->GetNetMode()==NM_DedicatedServer) return;
    const bool IsSlime=ResolveStyle()==ECombatVFXStyle::Slime;
    const AActor* TargetActor=Hit.Target.Get();
    const auto* TargetVFX=TargetActor?TargetActor->FindComponentByClass<UCombatVFXComponent>():nullptr;
    if(TargetVFX ? !TargetVFX->bPresentationEnabled : !bPresentationEnabled)return;
    const auto* TargetCharacter=Cast<ACharacter>(TargetActor);
    const auto* TargetMesh=TargetCharacter && TargetCharacter->GetMesh()?TargetCharacter->GetMesh()->GetSkeletalMeshAsset():nullptr;
    const bool TargetIsSlime=TargetVFX?TargetVFX->ResolveStyle()==ECombatVFXStyle::Slime:
        TargetMesh && TargetMesh->GetName().Contains(TEXT("Slime"));
    FVector Direction=TipDirectionAge<=.1f && !LastTipDirection.IsNearlyZero()?LastTipDirection:Hit.Normal;
    // Contact can arrive before the presentation tick for this pose.
    if (!IsSlime && bPreviousTipValid && Weapon.IsValid())
    {
        const FVector Motion=Weapon->GetComponentTransform().TransformPosition(FVector(0,0,-95))-PreviousTip;
        if (Motion.SizeSquared()>1.f && Motion.SizeSquared()<=FMath::Square(120.f)) Direction=Motion.GetSafeNormal();
    }
    if (IsSlime) Direction=GetOwner()->GetActorForwardVector();
    FVector PresentationPosition=Hit.Position;
    FVector PresentationNormal=Hit.Normal;
    // Combat uses capsule contacts. A wider render mesh can hide the exact point inside its body.
    // Move presentation only to the visible bounds along the recorded normal; payload and damage stay exact.
    if (TargetIsSlime)
    {
        int32 Triangles=0;
        const bool Resolved=CombatSurfaceContact::Resolve(TargetCharacter?TargetCharacter->GetMesh():nullptr,
            Hit.Position,Hit.Normal,PresentationPosition,PresentationNormal,Triangles);
#if !UE_BUILD_SHIPPING
        if (FParse::Param(FCommandLine::Get(),TEXT("CombatVFXReview")))
            UE_LOG(LogTemp,Display,TEXT("COMBAT_VFX_SURFACE target=%s resolved=%d triangles=%d contact=%s surface=%s displacement=%.3f"),
                *GetNameSafe(TargetActor),Resolved,Triangles,*Hit.Position.ToString(),*PresentationPosition.ToString(),
                FVector::Distance(Hit.Position,PresentationPosition));
#endif
    }
    else if (auto* Target=Cast<ACharacter>(Hit.Target.Get()))
    {
        auto* Mesh=Target->GetMesh();
        if (Mesh && Mesh->GetSkeletalMeshAsset())
        {
            const FBox Box=Mesh->Bounds.GetBox();
            // A body hit needs to read on the visible torso, even from a side camera.
            // Attack-normal projection can put its entire billboard behind clothing/arms.
            // Only presentation moves; the confirmed contact and all damage remain untouched.
            if (IsSlime && !TargetIsSlime && Box.IsValid)
                if (const auto* Camera=UGameplayStatics::GetPlayerCameraManager(this,0))
                {
                    PresentationPosition=Box.GetCenter();
                    PresentationPosition.Z=FMath::Clamp(Hit.Position.Z,Box.Min.Z+.1,Box.Max.Z-.1);
                    const FVector ViewDirection=(Camera->GetCameraLocation()-PresentationPosition).GetSafeNormal();
                    if (!ViewDirection.IsNearlyZero()) PresentationNormal=ViewDirection;
                }
            if (Box.IsValid && Box.IsInside(PresentationPosition))
            {
                double Exit=DBL_MAX;
                for (int32 Axis=0;Axis<3;++Axis)
                    if (FMath::Abs(PresentationNormal[Axis])>UE_SMALL_NUMBER)
                    {
                        const double Face=PresentationNormal[Axis]>0?Box.Max[Axis]:Box.Min[Axis];
                        Exit=FMath::Min(Exit,(Face-PresentationPosition[Axis])/PresentationNormal[Axis]);
                    }
                if (FMath::IsFinite(Exit) && Exit>=0) PresentationPosition+=PresentationNormal*Exit;
            }
        }
    }
    PresentationPosition+=PresentationNormal*2.f;
    auto Spawn=[&](EConstellationFXKind Kind,FLinearColor Color,float Scale)
    {
        auto* Effect=UConstellationFXLibrary::SpawnEffect(this,Kind,PresentationPosition,Direction,Color,Scale);
        if (Effect) Effect->SetOwner(GetOwner());
#if !UE_BUILD_SHIPPING
        if (FParse::Param(FCommandLine::Get(),TEXT("CombatVFXReview")))
            UE_LOG(LogTemp,Display,TEXT("COMBAT_VFX_CONFIRMED_SPAWN source=%s target=%s sourcestyle=%d targetslime=%d kind=%d actor=%s particles=%d origin=%s direction=%s"),
                *GetNameSafe(GetOwner()),*GetNameSafe(Hit.Target.Get()),int32(ResolveStyle()),TargetIsSlime,int32(Kind),*GetNameSafe(Effect),
                Effect?Effect->ParticleCount:0,*PresentationPosition.ToString(),*Direction.ToString());
#endif
    };
    if(TargetVFX && SpawnCue(TargetVFX->HitCue,PresentationPosition,Direction,false)) return;
    const EConstellationFXKind Kind=TargetIsSlime?EConstellationFXKind::SlimeHit:
        IsSlime?EConstellationFXKind::PlayerHit:EConstellationFXKind::SwordHit;
    const FLinearColor Color=TargetIsSlime?SlimeColor:IsSlime?UConstellationFXLibrary::CombatColor(Kind):SwordColor;
    Spawn(Kind,Color,UConstellationFXLibrary::CombatScale(Kind));
}
bool UCombatVFXComponent::SpawnCue(const FCombatVFXCue& Cue,const FVector& Position,const FVector& Direction,bool Attack)
{
    if(Cue.Mode==ECombatVFXCueMode::Default)return false;
    if(Cue.Mode==ECombatVFXCueMode::Disabled)return true;
    if(!FMath::IsFinite(Cue.Scale)||Cue.Scale<.01f||Cue.Scale>10 || !FMath::IsFinite(Cue.Duration)||Cue.Duration<.05f||Cue.Duration>10)return true;
    if(!FMath::IsFinite(Cue.Color.R)||!FMath::IsFinite(Cue.Color.G)||!FMath::IsFinite(Cue.Color.B)||!FMath::IsFinite(Cue.Color.A))return true;
    if(Cue.Mode==ECombatVFXCueMode::Builtin)
    {
        if(auto* Effect=UConstellationFXLibrary::SpawnEffect(this,Cue.Kind,Position,Direction,Cue.Color,Cue.Scale*UConstellationFXLibrary::CombatScale(Cue.Kind)))
        {Effect->SetOwner(GetOwner());Effect->SetLifeSpan(Cue.Duration);if(Attack){Effect->AttachToActor(GetOwner(),FAttachmentTransformRules::KeepWorldTransform);SlimeAttack=Effect;}}
    }
    else if(Cue.Mode==ECombatVFXCueMode::Niagara && Cue.System && FApp::CanEverRender())
    {
        CueBursts.RemoveAll([](const auto& C){return !C.IsValid();});
        if(!Attack && CueBursts.Num()>=32){if(auto* Old=CueBursts[0].Get())Old->DestroyComponent();CueBursts.RemoveAt(0);}
        // Spawn inactive so user parameters are ready before the first particle tick.
        auto* Component=UNiagaraFunctionLibrary::SpawnSystemAtLocation(this,Cue.System,Position,Direction.Rotation(),FVector(Cue.Scale),true,false,ENCPoolMethod::None,false);
        if(Component)
        {
            Component->SetVariableLinearColor(TEXT("User.Color"),Cue.Color);Component->SetVariableFloat(TEXT("User.Scale"),Cue.Scale);
            if(Attack){Component->AttachToComponent(GetOwner()->GetRootComponent(),FAttachmentTransformRules::KeepWorldTransform);ActiveTrail=Component;}else CueBursts.Add(Component);
            Component->Activate(true);
            FTimerHandle Expiry;TWeakObjectPtr<UNiagaraComponent> Weak=Component;
            GetWorld()->GetTimerManager().SetTimer(Expiry,[Weak]{if(auto* C=Weak.Get()){C->DeactivateImmediate();C->DestroyComponent();}},Cue.Duration,false);
        }
    }
    return true;
}
void UCombatVFXComponent::StopAttackPresentation()
{
    OpenWindows.Reset();
    if (ActiveTrail) { ActiveTrail->DeactivateImmediate(); ActiveTrail->DestroyComponent(); ActiveTrail=nullptr; }
    if (WeaponRibbon) { WeaponRibbon->DestroyComponent();WeaponRibbon=nullptr; }
    bPreviousTipValid=false;LastTipDirection=FVector::ZeroVector;TipDirectionAge=0.f;
    if (SlimeAttack.IsValid()) SlimeAttack->Destroy();
    SlimeAttack.Reset();
}
void UCombatVFXComponent::StopPresentation()
{
    StopAttackPresentation(); StepTravel=0.f;
    for(auto Weak:CueBursts)if(auto* Burst=Weak.Get()){Burst->DeactivateImmediate();Burst->DestroyComponent();}
    CueBursts.Reset();
    for(const auto& Effect:WarmupEffects) if(Effect.IsValid()) Effect->Destroy();
    WarmupEffects.Reset();
    UConstellationFXLibrary::StopEffectsForOwner(GetOwner());
}
bool UCombatVFXComponent::HasAttackPresentation() const
{
    return IsValid(WeaponRibbon) || IsValid(ActiveTrail) || (SlimeAttack.IsValid() && !SlimeAttack->IsActorBeingDestroyed());
}
int32 UCombatVFXComponent::GetWeaponRibbonSegments() const { return WeaponRibbon?WeaponRibbon->GetSegmentCount():0; }
bool UCombatVFXComponent::IsAuthoredTrailReady() const { const auto* System=SwordTrail.Get();return System && System->IsReadyToRun(); }
void UCombatVFXComponent::UpdateWeaponRibbon(float Delta)
{
    if (!WeaponRibbon || !Weapon.IsValid() || OpenWindows.IsEmpty()) return;
    const FVector Tip=Weapon->GetComponentTransform().TransformPosition(FVector(0,0,-95));
    TipDirectionAge+=Delta;
    const FVector Motion=Tip-PreviousTip;
    if (bPreviousTipValid && Delta<=.1f && Motion.SizeSquared()>1.f && Motion.SizeSquared()<=FMath::Square(120.f))
    { LastTipDirection=Motion.GetSafeNormal();TipDirectionAge=0.f; }
    else if (Delta>.1f || Motion.SizeSquared()>FMath::Square(120.f)) LastTipDirection=FVector::ZeroVector;
    PreviousTip=Tip;bPreviousTipValid=true;
    WeaponRibbon->AddTip(Tip,Delta);
}
void UCombatVFXComponent::UpdateFeet(float Delta)
{
    auto* Character=Cast<ACombatLabCharacter>(GetOwner());
    auto* Movement=Character?Character->GetCharacterMovement():nullptr;
    const float Speed=Character?Character->GetVelocity().Size2D():0.f;
    if (!Combat.IsValid() || !Movement || ResolveStyle()==ECombatVFXStyle::Slime || Character->bWorkbenchOpen ||
        Combat->GetHealth()<=0 || Combat->IsActing() || Combat->IsDodging() || Combat->IsHitReacting() ||
        !Movement->IsMovingOnGround() || Speed<FMath::Max(0.f,MinimumDustSpeed)) { StepTravel=0.f;return; }
    const float Distance=FMath::IsFinite(FootstepDistance)?FMath::Max(20.f,FootstepDistance):100.f;
    StepTravel=FMath::Min(Distance,StepTravel+Speed*Delta);
    if (StepTravel<Distance) return;
    StepTravel=0.f;bLeftFoot=!bLeftFoot;
    FVector Foot=Character->GetActorLocation()+Character->GetActorRightVector()*(bLeftFoot?-12.f:12.f);
    Foot.Z-=Character->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
    FHitResult Ground;
    FCollisionQueryParams Params(SCENE_QUERY_STAT(CombatFootFX),false,Character); Params.bReturnPhysicalMaterial=true;
    if (!GetWorld()->LineTraceSingleByChannel(Ground,Foot+FVector(0,0,30),Foot-FVector(0,0,45),ECC_Visibility,Params) || Ground.ImpactNormal.Z<.4f) return;
    auto* Component=Ground.GetComponent();
    if (Component && Component->ComponentHasTag(TEXT("FXNoDust"))) return;
    FCombatFootSurfaceFX Setting;
    const EPhysicalSurface Surface=UPhysicalMaterial::DetermineSurfaceType(Ground.PhysMaterial.Get());
    if (const auto* Configured=SurfaceEffects.Find(Surface)) Setting=*Configured;
    if (Component && Component->ComponentHasTag(TEXT("FXWater"))) Setting.bWater=true;
    // Existing project materials have no registered surface types; explicit surface overrides take priority.
    if (!SurfaceEffects.Contains(Surface) && Ground.PhysMaterial.IsValid())
    {
        const FString Name=Ground.PhysMaterial->GetName();
        if (Name.Contains(TEXT("Water"))) Setting.bWater=true;
        else if (Name.Contains(TEXT("Metal")) || Name.Contains(TEXT("Glass"))) Setting.bSuppressDust=true;
        else if (Name.Contains(TEXT("Stone")) || Name.Contains(TEXT("Concrete"))) Setting.Color=FLinearColor(.5f,.48f,.43f,.35f);
    }
    if (Setting.bSuppressDust) return;
    if (auto* Effect=UConstellationFXLibrary::SpawnEffect(this,Setting.bWater?EConstellationFXKind::WaterRipple:EConstellationFXKind::RunDust,
        Ground.ImpactPoint+Ground.ImpactNormal*2.f,Ground.ImpactNormal,Setting.bWater?FLinearColor(.35f,.7f,.85f,.5f):Setting.Color,Setting.bWater?.4f:.8f)) Effect->SetOwner(GetOwner());
}
void UCombatVFXComponent::TickComponent(float Delta,ELevelTick TickType,FActorComponentTickFunction* TickFunction)
{
    Super::TickComponent(Delta,TickType,TickFunction);
    if (!bPresentationEnabled)
    {
        if (HasAttackPresentation() || !OpenWindows.IsEmpty()) StopPresentation();
        return;
    }
    if (!IsValid(GetOwner()) || GetWorld()->GetNetMode()==NM_DedicatedServer || !FMath::IsFinite(Delta) || Delta<=0) return;
    UpdateWeaponRibbon(Delta);
    UpdateFeet(Delta);
}
void UCombatVFXComponent::EndPlay(const EEndPlayReason::Type Reason)
{
    Initialize(nullptr); Super::EndPlay(Reason);
}
