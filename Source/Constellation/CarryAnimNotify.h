#pragma once
#include "CoreMinimal.h"
#include "Animation/AnimNotifies/AnimNotify.h"
#include "CarryAnimNotify.generated.h"
UENUM(BlueprintType)
enum class ECarryContact : uint8 { Pickup, Place, Throw };
UCLASS()
class CONSTELLATION_API UCarryAnimNotify : public UAnimNotify
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Carry") ECarryContact Contact = ECarryContact::Pickup;
    virtual void Notify(USkeletalMeshComponent* Mesh, UAnimSequenceBase* Animation, const FAnimNotifyEventReference& Reference) override;
};
