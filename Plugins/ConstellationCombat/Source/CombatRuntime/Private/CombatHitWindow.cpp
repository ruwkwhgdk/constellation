#include "CombatHitWindow.h"
#include "CombatAbilitySystem.h"
#include "Components/SkeletalMeshComponent.h"
#include "Animation/ActiveMontageInstanceScope.h"
namespace
{
    UCombatAbilitySystem* System(USkeletalMeshComponent* Mesh)
    {
        return Mesh && Mesh->GetOwner() ? Mesh->GetOwner()->FindComponentByClass<UCombatAbilitySystem>() : nullptr;
    }
    int32 Instance(const FAnimNotifyEventReference& Ref)
    {
        const auto* Context = Ref.GetContextData<UE::Anim::FAnimNotifyMontageInstanceContext>();
        return Context ? Context->MontageInstanceID : INDEX_NONE;
    }
}
void UCombatHitWindow::NotifyBegin(USkeletalMeshComponent* Mesh, UAnimSequenceBase*, float, const FAnimNotifyEventReference& Ref)
{ if (auto* ASC = System(Mesh)) ASC->OpenHitWindow(WindowId, Instance(Ref)); }
void UCombatHitWindow::NotifyTick(USkeletalMeshComponent* Mesh, UAnimSequenceBase*, float, const FAnimNotifyEventReference& Ref)
{ if (auto* ASC = System(Mesh)) ASC->TickHitWindow(WindowId, Instance(Ref)); }
void UCombatHitWindow::NotifyEnd(USkeletalMeshComponent* Mesh, UAnimSequenceBase*, const FAnimNotifyEventReference& Ref)
{ if (auto* ASC = System(Mesh)) ASC->CloseHitWindow(WindowId, Instance(Ref)); }
