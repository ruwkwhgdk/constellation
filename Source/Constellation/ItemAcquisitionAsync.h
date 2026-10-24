#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintAsyncActionBase.h"
#include "ItemAcquisitionTypes.h"
#include "ItemAcquisitionAsync.generated.h"
class UItemAcquisitionSubsystem;
class UItemAcquisitionDefinition;
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FItemAcquisitionResult);
UCLASS()
class CONSTELLATION_API UItemAcquisitionAsync : public UBlueprintAsyncActionBase
{
 GENERATED_BODY()
public:
 // An unassigned key resolves the live IA_Interact mapping. No item is granted.
 UFUNCTION(BlueprintCallable,Category="Item Acquisition",meta=(BlueprintInternalUseOnly="true",WorldContext="WorldContextObject",AutoCreateRefTerm="ConfirmKey",ExposedAsyncProxy="Request"))
 static UItemAcquisitionAsync* ShowSpecialItem(UObject* WorldContextObject,const FItemAcquisitionPresentation& Presentation,FKey ConfirmKey);
 UFUNCTION(BlueprintCallable,Category="Item Acquisition",meta=(BlueprintInternalUseOnly="true",WorldContext="WorldContextObject",AutoCreateRefTerm="ConfirmKey",ExposedAsyncProxy="Request",AdvancedDisplay="ConfirmKey",CPP_Default_Quantity="1"))
 static UItemAcquisitionAsync* ShowSpecialItemDefinition(UObject* WorldContextObject,UItemAcquisitionDefinition* Definition,int32 Quantity,FKey ConfirmKey);
 UPROPERTY(BlueprintAssignable) FItemAcquisitionResult Completed;
 UPROPERTY(BlueprintAssignable) FItemAcquisitionResult Cancelled;
 UFUNCTION(BlueprintCallable,Category="Item Acquisition") void Cancel();
 virtual void Activate()override;
private:
 UPROPERTY() FItemAcquisitionPresentation Payload;
 TWeakObjectPtr<UObject> Context;
 TWeakObjectPtr<UItemAcquisitionSubsystem> Subsystem;
 FKey Key;FGuid RequestId;bool bResolved=false,bActivated=false;
 void Resolve(bool Success);
};
