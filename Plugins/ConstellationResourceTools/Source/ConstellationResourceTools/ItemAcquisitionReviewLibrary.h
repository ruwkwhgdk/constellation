#pragma once
#include "CoreMinimal.h"
#include "InputCoreTypes.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "ItemAcquisitionReviewLibrary.generated.h"
class UTexture2D;
UCLASS()
class UItemAcquisitionReviewLibrary : public UBlueprintFunctionLibrary
{
 GENERATED_BODY()
public:
 UFUNCTION(BlueprintCallable) static FGuid ShowReviewCard(UObject* Context,UTexture2D* Sprite,const FText& Name,const FText& Description,int32 Quantity);
 UFUNCTION(BlueprintCallable) static bool SendReviewKey(FKey Key,bool Down);
 UFUNCTION(BlueprintCallable) static FString ReviewResults();
};
