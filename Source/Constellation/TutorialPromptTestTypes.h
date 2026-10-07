#pragma once

#include "TutorialPromptWidget.h"
#include "GameFramework/PlayerController.h"
#include "TutorialPromptTestTypes.generated.h"

// Transient native fixtures keep test access out of the gameplay widget API.
UCLASS(Transient, NotBlueprintable)
class ATutorialPromptTestController : public APlayerController
{
	GENERATED_BODY()
public:
	FString LastInputMode;
	virtual void SetInputMode(const FInputModeDataBase& Mode) override
	{
#if UE_ENABLE_DEBUG_DRAWING
		LastInputMode = Mode.GetDebugDisplayName();
#endif
		Super::SetInputMode(Mode);
	}
};

UCLASS(Transient, NotBlueprintable)
class UTutorialPromptTestWidget : public UTutorialPromptWidget
{
	GENERATED_BODY()
public:
	void ConstructForTest() { NativeConstruct(); }
	void DestructForTest() { NativeDestruct(); }
	int32 DismissCount = 0;
	UFUNCTION()
	void RecordDismissal() { ++DismissCount; }
};
