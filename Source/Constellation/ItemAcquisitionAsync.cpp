#include "ItemAcquisitionAsync.h"
#include "ItemAcquisitionSubsystem.h"
#include "ItemAcquisitionDefinition.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
UItemAcquisitionAsync* UItemAcquisitionAsync::ShowSpecialItem(UObject* WorldContextObject,const FItemAcquisitionPresentation& Presentation,FKey ConfirmKey)
{
 auto* Node=NewObject<UItemAcquisitionAsync>();Node->Context=WorldContextObject;Node->Payload=Presentation;Node->Key=ConfirmKey;
 if(WorldContextObject)Node->RegisterWithGameInstance(WorldContextObject);return Node;
}
void UItemAcquisitionAsync::Activate()
{
 if(bActivated||bResolved)return;bActivated=true;
 auto* World=GEngine?GEngine->GetWorldFromContextObject(Context.Get(),EGetWorldErrorMode::ReturnNull):nullptr;
 if(!World){Resolve(false);return;}
 Subsystem=World->GetSubsystem<UItemAcquisitionSubsystem>();if(!Subsystem.IsValid()){Resolve(false);return;}
 const TWeakObjectPtr<UItemAcquisitionAsync> WeakThis(this);
 RequestId=Subsystem->Enqueue(Payload,Key,Context.Get(),[WeakThis](bool Success){if(auto* Node=WeakThis.Get())Node->Resolve(Success);});
 if(!RequestId.IsValid())Resolve(false);
}
UItemAcquisitionAsync* UItemAcquisitionAsync::ShowSpecialItemDefinition(UObject* ContextObject,UItemAcquisitionDefinition* Definition,int32 Quantity,FKey ConfirmKey)
{
 FItemAcquisitionPresentation P;if(IsValid(Definition)){P=Definition->Presentation;P.Quantity=Quantity;}
 return ShowSpecialItem(ContextObject,P,ConfirmKey);
}
void UItemAcquisitionAsync::Cancel(){if(bResolved)return;if(Subsystem.IsValid()&&RequestId.IsValid())Subsystem->Cancel(RequestId);else Resolve(false);}
void UItemAcquisitionAsync::Resolve(bool Success)
{
 if(bResolved)return;bResolved=true;RequestId.Invalidate();
 if(Success)Completed.Broadcast();else Cancelled.Broadcast();SetReadyToDestroy();
}
