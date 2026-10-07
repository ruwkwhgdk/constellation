#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "CarryNoticeWidget.generated.h"
class UTextBlock;
UCLASS()
class CONSTELLATION_API UCarryNoticeWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    void ShowMessage(const FText& Message,float Duration);
protected:
    virtual void NativeOnInitialized() override;
private:
    UPROPERTY(Transient) TObjectPtr<UTextBlock> Label;
    FTimerHandle HideTimer;
};
