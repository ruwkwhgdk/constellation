#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "UObject/UnrealType.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSchoolOpeningContractTest,"Constellation.SchoolOpening.Contract",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FSchoolOpeningContractTest::RunTest(const FString&)
{
 UClass* C=FindObject<UClass>(nullptr,TEXT("/Script/Constellation.SchoolOpeningSceneActor"));
 if(!TestNotNull(TEXT("School opening runtime is available"),C))return false;
 TestNotNull(TEXT("Editor action entry"),C->FindFunctionByName(TEXT("RunCue")));
 TestNotNull(TEXT("Completion state observable"),FindFProperty<FBoolProperty>(C,TEXT("bCompleted")));
 TestNotNull(TEXT("Safe player handoff configurable"),FindFProperty<FStructProperty>(C,TEXT("ExitTransform")));
 return true;
}
#include "SchoolOpeningSceneActor.h"
#include "TutorialPromptWidget.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSchoolOpeningTutorialRetryTest,"Constellation.SchoolOpening.TutorialRetry",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FSchoolOpeningTutorialRetryTest::RunTest(const FString&)
{
 auto* World=UWorld::CreateWorld(EWorldType::Game,false);GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);World->InitializeActorsForPlay(FURL());
 auto* Stage=World->SpawnActor<ASchoolOpeningSceneActor>();Stage->bPending=true;
 auto* Widget=NewObject<UTutorialPromptWidget>(World);Widget->bOpeningDeferred=true;
 TestEqual(TEXT("Widget uses test world"),Widget->GetWorld(),World);
 // This is the delayed timer callback after cancellation followed by a new opening.
 Widget->ActivatePrompt();TestTrue(TEXT("Retry keeps tutorial deferred"),Widget->bOpeningDeferred);
 Widget->NativeDestruct();GEngine->DestroyWorldContext(World);World->DestroyWorld(false);return true;
}
#endif
