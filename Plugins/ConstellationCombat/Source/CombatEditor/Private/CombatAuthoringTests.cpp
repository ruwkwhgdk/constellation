#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "CombatLabEditorLibrary.h"
#include "CombatActionDefinition.h"
#include "CombatHitWindow.h"
#include "Animation/AnimMontage.h"
#include "UObject/Package.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatAuthoredWindowsTest,"Constellation.CombatCore.AuthoredHitWindows",
 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatAuthoredWindowsTest::RunTest(const FString&)
{
 auto* Source=LoadObject<UAnimMontage>(nullptr,TEXT("/Game/Constellation/Characters/Heroine/Refined/Animations/AM_player_heroine_new_Attack01_Horizontal.AM_player_heroine_new_Attack01_Horizontal"));
 if(!TestNotNull(TEXT("Source montage"),Source))return false;
 const int32 Count=Source->Notifies.Num();
 TestFalse(TEXT("Protected source cannot be edited"),UCombatLabEditorLibrary::ConfigureAuthoredHitWindows(Source,{TEXT("A")},{.1f},{.2f}));
 auto* Package=CreatePackage(*(TEXT("/Game/Constellation/Review/CombatRecipes/Test_")+FGuid::NewGuid().ToString(EGuidFormats::Digits)));
 auto* Copy=DuplicateObject<UAnimMontage>(Source,Package,TEXT("AM_Test"));
 TestTrue(TEXT("Two named windows configured"),UCombatLabEditorLibrary::ConfigureAuthoredHitWindows(Copy,{TEXT("A"),TEXT("B")},{.1f,.3f},{.2f,.4f}));
 auto* Action=NewObject<UCombatActionDefinition>();Action->Montage=Copy;FString Reason;
 TestTrue(TEXT("Configured action native validation"),Action->Validate(Reason));
 const int32 After=Copy->Notifies.Num();
 TestFalse(TEXT("Duplicate window ids rejected"),UCombatLabEditorLibrary::ConfigureAuthoredHitWindows(Copy,{TEXT("A"),TEXT("A")},{.1f,.3f},{.2f,.4f}));
 TestEqual(TEXT("Invalid edit is atomic"),Copy->Notifies.Num(),After);
 TestEqual(TEXT("Source not touched"),Source->Notifies.Num(),Count);
 Package->SetDirtyFlag(false);return true;
}
#endif
