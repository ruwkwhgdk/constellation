#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "SubwayPortalTransform.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSubwayPortalPoseTest, "Constellation.Subway.PortalPose",
                                 EAutomationTestFlags::EditorContext |
                                     EAutomationTestFlags::EngineFilter)
bool FSubwayPortalPoseTest::RunTest(const FString &)
{
    const FTransform Source(FRotator(0, 0, 0), FVector(4700, -20500, 9640));
    const FTransform Destination(FRotator(0, 90, 0), FVector(-1500, -800, 360));
    const auto P = SubwayPortalTransform(Source, Destination, FVector(4720, -20570, 9736),
                                         FRotator(-12, 22, 0).Quaternion(), FVector(320, 40, -15));
    TestTrue(TEXT("Keeps lateral offset and capsule height"),
             P.Location.Equals(FVector(-1430, -780, 456), .01));
    TestTrue(TEXT("Rotates velocity without stopping or changing speed"),
             P.Velocity.Equals(FVector(-40, 320, -15), .01));
    TestTrue(TEXT("Keeps look pitch and relative yaw"),
             P.Rotation.Rotator().Equals(FRotator(-12, 112, 0), .01));
    const FTransform ReturnSource(FRotator(0, -90, 0), FVector(-1500, -800, 360));
    const FTransform ReturnDestination(FRotator(0, 180, 0), FVector(4700, -20500, 9640));
    const auto Back =
        SubwayPortalTransform(ReturnSource, ReturnDestination, P.Location, P.Rotation, P.Velocity);
    TestTrue(TEXT("Round trip preserves position"),
             Back.Location.Equals(FVector(4720, -20570, 9736), .01));
    TestTrue(TEXT("Round trip preserves velocity"),
             Back.Velocity.Equals(FVector(320, 40, -15), .01));
    return true;
}
#endif
