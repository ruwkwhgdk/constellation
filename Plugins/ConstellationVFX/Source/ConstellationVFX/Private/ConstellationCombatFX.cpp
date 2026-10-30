#include "ConstellationCombatFX.h"
#include "ConstellationSwordRibbonComponent.h"
#include "ConstellationFXActor.h"
#include "Engine/World.h"

FConstellationTrailProfile UConstellationCombatFX::TrailProfile(EConstellationAttackTrail Kind)
{
    FConstellationTrailProfile P;
    switch(Kind)
    {
    case EConstellationAttackTrail::Light2:P.Width=26.f;P.Lifetime=.17f;break;
    case EConstellationAttackTrail::Light3:P.Width=30.f;P.Lifetime=.20f;P.Brightness=1.85f;break;
    case EConstellationAttackTrail::Heavy1:P.Width=38.f;P.Lifetime=.24f;P.Brightness=1.9f;break;
    case EConstellationAttackTrail::Heavy2:P.Width=44.f;P.Lifetime=.28f;P.Brightness=2.f;break;
    case EConstellationAttackTrail::LightParry:P.Width=28.f;P.Lifetime=.12f;P.Brightness=2.2f;P.Color=FLinearColor(1.f,.87f,.62f,1.f);break;
    case EConstellationAttackTrail::HeavyParry:P.Width=46.f;P.Lifetime=.26f;P.Brightness=2.1f;P.Color=FLinearColor(1.f,.78f,.42f,1.f);break;
    default:break;
    }
    return P;
}
void UConstellationCombatFX::ConfigureTrail(UConstellationSwordRibbonComponent* Ribbon,EConstellationAttackTrail Kind)
{
    if(!IsValid(Ribbon))return;
    const auto P=TrailProfile(Kind);Ribbon->ConfigureShape(P.Width,P.Lifetime,P.Brightness);Ribbon->Configure(P.Color);
}
AConstellationFXActor* UConstellationCombatFX::SpawnContact(const UObject* Context,EConstellationContactResult Result,EConstellationFXKind TargetHitKind,FVector Position,FVector Direction)
{
    EConstellationFXKind Kind;
    switch(Result)
    {
    case EConstellationContactResult::Hit:Kind=TargetHitKind;break;
    case EConstellationContactResult::Guard:Kind=EConstellationFXKind::SwordBlock;break;
    case EConstellationContactResult::PerfectGuard:Kind=EConstellationFXKind::SwordParry;break;
    default:return nullptr;
    }
    return UConstellationFXLibrary::SpawnEffect(Context,Kind,Position,Direction,UConstellationFXLibrary::CombatColor(Kind),UConstellationFXLibrary::CombatScale(Kind));
}
AConstellationFXActor* UConstellationGroggyFXComponent::Spawn(EConstellationFXKind Kind)
{
    if(!IsValid(GetOwner()) || !GetWorld() || GetWorld()->GetNetMode()==NM_DedicatedServer)return nullptr;
    auto* FX=UConstellationFXLibrary::SpawnEffect(this,Kind,GetOwner()->GetActorTransform().TransformPosition(LocalOffset),FVector::UpVector,UConstellationFXLibrary::CombatColor(Kind),Scale);
    if(FX)
    {
        FX->SetOwner(GetOwner());
        if(GetOwner()->GetRootComponent())FX->AttachToActor(GetOwner(),FAttachmentTransformRules::KeepWorldTransform);
        Effects.RemoveAll([](const auto& Item){return !Item.IsValid() || Item->IsActorBeingDestroyed();});
        Effects.Add(FX);
    }
    return FX;
}
void UConstellationGroggyFXComponent::SetGroggy(bool Active)
{
    if(bGroggy==Active)
    {
        // A world-wide presentation reset may have destroyed the held actor.
        // Reconciliation restores only the loop, never replays groggy entry.
        if(Active && (!Hold.IsValid() || Hold->IsActorBeingDestroyed()))Hold=Spawn(EConstellationFXKind::GroggyHold);
        return;
    }
    StopPresentation();
    bGroggy=Active;
    if(Active){Spawn(EConstellationFXKind::GroggyEnter);Hold=Spawn(EConstellationFXKind::GroggyHold);}
    else
    {
        if(Hold.IsValid())Hold->Destroy();Hold.Reset();
        Spawn(EConstellationFXKind::GroggyExit);
    }
}
void UConstellationGroggyFXComponent::StopPresentation()
{
    for(auto FX:Effects)if(FX.IsValid())FX->Destroy();
    Effects.Reset();Hold.Reset();bGroggy=false;
}
void UConstellationGroggyFXComponent::EndPlay(const EEndPlayReason::Type Reason)
{
    StopPresentation();Super::EndPlay(Reason);
}
