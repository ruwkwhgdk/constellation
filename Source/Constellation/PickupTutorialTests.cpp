#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "TutorialPromptTestTypes.h"
#include "PickupTutorialTrigger.h"
#include "Components/BoxComponent.h"
#include "Engine/World.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FPickupTutorialTest,"Constellation.Audit.TutorialPrompt.PickupInstruction",
 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FPickupTutorialTest::RunTest(const FString&)
{
 auto* Prompt=NewObject<UTutorialPromptTestWidget>();
 Prompt->Action=ETutorialPromptAction::PickUp;
 Prompt->TargetKeys={EKeys::F};
 TestEqual(TEXT("Requested pickup copy"),Prompt->GetInstructionText().ToString(),FString(TEXT("F를 눌러 물건을 들 수 있습니다.")));
 TestEqual(TEXT("Existing eight-second lifetime"),Prompt->HoldSeconds,8.f);
 TestFalse(TEXT("Toast does not steal keyboard focus"),Prompt->IsFocusable());
 UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
 auto* Area=World->SpawnActor<APickupTutorialTrigger>();
 Area->Tick(.1f);
 TestFalse(TEXT("No player cannot consume lesson"),Area->bHasShown);
 TestEqual(TEXT("Area never blocks movement"),Area->Area->GetCollisionEnabled(),ECollisionEnabled::NoCollision);
 World->DestroyWorld(false);
 return true;
}
#endif
