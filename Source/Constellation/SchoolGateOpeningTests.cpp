#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "SchoolGateOpeningComponent.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSchoolGateTimingTest,"Constellation.Gate.TwoEffortTiming",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FSchoolGateTimingTest::RunTest(const FString&)
{
 TestEqual(TEXT("Contact preparation stays closed"),USchoolGateOpeningComponent::OpeningAngle(.85f),0.f);
 TestEqual(TEXT("First effort"),USchoolGateOpeningComponent::OpeningAngle(1.65f),5.f);
 TestEqual(TEXT("Second effort starts"),USchoolGateOpeningComponent::OpeningAngle(2.f),4.8f);
 TestEqual(TEXT("More opening while pushing"),USchoolGateOpeningComponent::OpeningAngle(5.f),20.f);
 TestEqual(TEXT("Continued opening after release"),USchoolGateOpeningComponent::OpeningAngle(5.8f),24.f);
 TestEqual(TEXT("Fully open before hands lower"),USchoolGateOpeningComponent::OpeningAngle(8.f),90.f);
 const float E=.001f;
 const float Before=(USchoolGateOpeningComponent::OpeningAngle(5.8f)-USchoolGateOpeningComponent::OpeningAngle(5.8f-E))/E;
 const float After=(USchoolGateOpeningComponent::OpeningAngle(5.8f+E)-USchoolGateOpeningComponent::OpeningAngle(5.8f))/E;
 TestTrue(TEXT("No speed jump on release"),FMath::Abs(After-Before)<.2f);
 TestEqual(TEXT("Open during recovery"),USchoolGateOpeningComponent::OpeningAngle(8.5f),90.f);
 TestEqual(TEXT("Clamp before start"),USchoolGateOpeningComponent::OpeningAngle(-1.f),0.f);
 return true;
}
#endif
