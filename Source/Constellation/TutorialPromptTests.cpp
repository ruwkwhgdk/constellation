#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "TutorialPromptTestTypes.h"
#include "Engine/Engine.h"
#include "Engine/LocalPlayer.h"
#include "Engine/World.h"

#if UE_ENABLE_DEBUG_DRAWING
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FTutorialPromptRemovalTest,
	"Constellation.Audit.TutorialPrompt.RemovalRestoresInput",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FTutorialPromptRemovalTest::RunTest(const FString&)
{
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
	if (!TestNotNull(TEXT("Transient world"), World)) return false;
	ATutorialPromptTestController* PC = World->SpawnActor<ATutorialPromptTestController>();
	if (!TestNotNull(TEXT("Test controller"), PC))
	{
		World->DestroyWorld(false);
		return false;
	}
	ULocalPlayer* Player = NewObject<ULocalPlayer>(GEngine);
	Player->PlayerController = PC;
	PC->Player = Player;
	// This world has not initialized actors, so SpawnActor has not called the
	// controller's PostInitializeComponents registration used by local-player lookup.
	World->AddController(PC);
	auto MakePrompt = [World, PC]()
	{
		UTutorialPromptTestWidget* Prompt = NewObject<UTutorialPromptTestWidget>(World);
		Prompt->SetOwningPlayer(PC);
		Prompt->OnTutorialPromptDismissed.AddDynamic(Prompt, &UTutorialPromptTestWidget::RecordDismissal);
		return Prompt;
	};
	UTutorialPromptTestWidget* First = MakePrompt();
	if (!TestEqual(TEXT("Owning player resolves in transient world"), First->GetOwningPlayer(), static_cast<APlayerController*>(PC)))
	{
		World->DestroyWorld(false);
		return false;
	}
	First->ConstructForTest();
	TestTrue(TEXT("Visible tutorial shows cursor"), PC->bShowMouseCursor != 0);
	TestEqual(TEXT("Visible tutorial requests UI input"), PC->LastInputMode, FInputModeUIOnly().GetDebugDisplayName());
	// Exercise the native lifecycle hook reached by external widget removal.
	First->DestructForTest();
	TestFalse(TEXT("External removal hides cursor"), PC->bShowMouseCursor != 0);
	TestEqual(TEXT("External removal restores game input"), PC->LastInputMode, FInputModeGameOnly().GetDebugDisplayName());
	TestEqual(TEXT("Removal does not complete tutorial gameplay"), First->DismissCount, 0);
	First->ConstructForTest();
	UTutorialPromptTestWidget* Second = MakePrompt();
	Second->ConstructForTest();
	TestEqual(TEXT("Replacement dismisses the first prompt once"), First->DismissCount, 1);
	First->DestructForTest();
	TestTrue(TEXT("Late destruction preserves the replacement cursor"), PC->bShowMouseCursor != 0);
	TestEqual(TEXT("Late destruction preserves replacement input"), PC->LastInputMode, FInputModeUIOnly().GetDebugDisplayName());
	Second->Dismiss();
	Second->Dismiss();
	TestEqual(TEXT("Explicit dismissal broadcasts only once"), Second->DismissCount, 1);
	TestFalse(TEXT("Explicit dismissal restores cursor"), PC->bShowMouseCursor != 0);
	Second->DestructForTest();
	World->DestroyWorld(false);
	return true;
}
#endif
#endif
