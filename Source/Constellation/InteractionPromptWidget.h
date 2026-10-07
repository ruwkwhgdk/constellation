#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "InteractionPromptWidget.generated.h"
class UTextBlock;
class UTexture2D;
class UImage;
UCLASS()
class CONSTELLATION_API UInteractionPromptWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    void SetBackgroundTexture(UTexture2D* Texture);
    void SetKeyBackgroundTexture(UTexture2D* Texture);
    void SetPrompt(const FText& Key,const FText& Action);
protected:
    virtual void NativeOnInitialized() override;
private:
    UPROPERTY(Transient) TObjectPtr<UImage> Background;
    UPROPERTY(Transient) TObjectPtr<UImage> KeyBackground;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> KeyLabel;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> ActionLabel;
};
