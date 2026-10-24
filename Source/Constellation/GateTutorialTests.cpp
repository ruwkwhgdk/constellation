#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "TutorialPromptWidget.h"
#include "UObject/UnrealType.h"
#include "Engine/Texture2D.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGateTutorialTextTest,"Constellation.Audit.TutorialPrompt.GateInstruction",
 EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FGateTutorialTextTest::RunTest(const FString&)
{
 UClass* Class=LoadClass<UTutorialPromptWidget>(nullptr,TEXT("/Game/Constellation/UI/Widgets/WBP_Tutorial.WBP_Tutorial_C"));
 if(!TestNotNull(TEXT("Authored tutorial class"),Class))return false;
 auto* Prompt=NewObject<UTutorialPromptWidget>(GetTransientPackage(),Class);
 auto* Image=FindFProperty<FObjectPropertyBase>(Class,TEXT("Image"));
 if(!TestNotNull(TEXT("Legacy lesson image property"),Image))return false;
 auto* Texture=LoadObject<UTexture2D>(nullptr,TEXT("/Game/Constellation/UI/Art/Tutorial_Interact.Tutorial_Interact"));
 if(!TestNotNull(TEXT("Gate lesson identity"),Texture))return false;
 Image->SetObjectPropertyValue_InContainer(Prompt,Texture);
 Prompt->TargetKeys={EKeys::F};
 TestEqual(TEXT("Complete requested gate instruction"),Prompt->GetInstructionText().ToString(),FString(TEXT("문 앞에서 F를 눌러 문을 여세요.")));
 Prompt->Action=ETutorialPromptAction::PickUp;
 TestEqual(TEXT("Pickup remains independent"),Prompt->GetInstructionText().ToString(),FString(TEXT("F를 눌러 물건을 들 수 있습니다.")));
 Prompt->Action=ETutorialPromptAction::Auto;
 Image->SetObjectPropertyValue_InContainer(Prompt,nullptr);
 TestEqual(TEXT("F alone does not identify a door"),Prompt->GetInstructionText().ToString(),FString(TEXT("F를 눌러 ")));
 return true;
}
#endif
