#pragma once
#include "CoreMinimal.h"
#include "Animation/AnimNotifies/AnimNotifyState.h"
#include "CombatHitWindow.generated.h"
UCLASS(meta=(DisplayName="Combat Hit Window"))
class COMBATRUNTIME_API UCombatHitWindow : public UAnimNotifyState
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, Category="Combat") FName WindowId = TEXT("Swing");
    virtual void NotifyBegin(USkeletalMeshComponent* Mesh, UAnimSequenceBase* Animation, float Duration, const FAnimNotifyEventReference& Ref) override;
    virtual void NotifyTick(USkeletalMeshComponent* Mesh, UAnimSequenceBase* Animation, float Delta, const FAnimNotifyEventReference& Ref) override;
    virtual void NotifyEnd(USkeletalMeshComponent* Mesh, UAnimSequenceBase* Animation, const FAnimNotifyEventReference& Ref) override;
};
