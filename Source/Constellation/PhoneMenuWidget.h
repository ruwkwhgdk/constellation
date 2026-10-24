#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "PhoneMenuWidget.generated.h"
class SButton;
class STextBlock;
UCLASS()
class CONSTELLATION_API UPhoneMenuWidget : public UUserWidget
{
 GENERATED_BODY()
public:
 FSimpleDelegate OnClose;
 void FocusFirst();
 void SelectEntry(int32 Index);
protected:
 virtual TSharedRef<SWidget> RebuildWidget() override;
 virtual FReply NativeOnKeyDown(const FGeometry&,const FKeyEvent&) override;
 virtual FReply NativeOnKeyUp(const FGeometry&,const FKeyEvent&) override {return FReply::Handled();}
private:
 TArray<TSharedPtr<SButton>> Buttons;
 TSharedPtr<STextBlock> Status;
};
