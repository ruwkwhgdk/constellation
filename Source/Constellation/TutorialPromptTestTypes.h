#pragma once

#include "TutorialPromptWidget.h"
#include "GameFramework/PlayerController.h"
#include "Input/Events.h"
#include "TutorialPromptTestTypes.generated.h"

// Transient native fixtures keep test access out of the gameplay widget API.
UCLASS(Transient, NotBlueprintable)
class ATutorialPromptTestController : public APlayerController
{
	GENERATED_BODY()
public:
	FString LastInputMode;
	int32 InputModeCalls = 0;
	virtual void SetInputMode(const FInputModeDataBase& Mode) override
	{
		++InputModeCalls;
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
 void AdvanceForTest(float Delta) { AdvanceToast(Delta); }
 int32 StackIndexForTest() const { return GetStackIndex(); }
 bool KeyForTest(FKey Key) { return NativeOnKeyDown(FGeometry(), FKeyEvent(Key, FModifierKeysState(), 0, false, 0, 0)).IsEventHandled(); }
 bool MouseForTest() { return NativeOnMouseButtonDown(FGeometry(), FPointerEvent()).IsEventHandled(); }
	int32 DismissCount = 0;
	UFUNCTION()
	void RecordDismissal() { ++DismissCount; }
};
