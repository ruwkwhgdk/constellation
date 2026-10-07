#pragma once
#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "CombatActionGate.generated.h"
UINTERFACE(BlueprintType)
class COMBATRUNTIME_API UCombatActionGate : public UInterface { GENERATED_BODY() };
class COMBATRUNTIME_API ICombatActionGate
{
 GENERATED_BODY()
public:
 UFUNCTION(BlueprintNativeEvent,BlueprintCallable,Category="Combat|Integration")
 bool AllowsCombatAction(FString& Reason) const;
 virtual bool AllowsCombatAction_Implementation(FString& Reason) const {Reason.Reset();return true;}
};
