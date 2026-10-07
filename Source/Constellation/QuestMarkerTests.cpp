#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "QuestMarkerProjection.h"
#include "SceneView.h"
#include <limits>

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FQuestMarkerBehindCameraTest, "Constellation.Quest.MarkerBehindCamera",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FQuestMarkerBehindCameraTest::RunTest(const FString&)
{
	// Camera-space X/Y are right/up; Z becomes homogeneous W (camera depth).
	const FMatrix Projection(FPlane(1, 0, 0, 0), FPlane(0, 1, 0, 0),
		FPlane(0, 0, 0, 1), FPlane(0, 0, 1, 0));
	const FVector2D ViewSize(1920, 1080);
	FVector2D ScreenPosition(123, 456);
	TestFalse(TEXT("Engine rejects a target behind the camera"),
		FSceneView::ProjectWorldToScreen(FVector(1, 0, -1), FIntRect(0, 0, 1920, 1080), Projection, ScreenPosition));
	TestTrue(TEXT("Rejected engine projection leaves its output untouched"), ScreenPosition.Equals(FVector2D(123, 456)));

	struct FCase { FVector Target; FVector2D ExpectedEdge; };
	const FCase Cases[] = {
		{ FVector(1, 0, -1), FVector2D(912, 0) },
		{ FVector(-1, 0, -1), FVector2D(-912, 0) },
		{ FVector(0, 1, -1), FVector2D(0, -492) },
		{ FVector(0, -1, -1), FVector2D(0, 492) },
		{ FVector(1, 0, 0), FVector2D(912, 0) },
		{ FVector(0, 0, -1), FVector2D(0, -492) },
		{ FVector(1, 1, -1), FVector2D(874.6666667, -492) }
	};
	for (const FCase& Case : Cases)
	{
		FVector2D Direction;
		TestTrue(TEXT("Behind-camera/camera-plane target has a finite direction"),
			QuestMarkerProjection::GetBehindCameraDirection(Case.Target, Projection, ViewSize, Direction));
		TestTrue(TEXT("Arrow reaches the correct edge without mirroring"),
			QuestMarkerProjection::ClampDirectionToRectEdge(Direction, FVector2D(912, 492)).Equals(Case.ExpectedEdge, .001));
	}
	FVector2D Direction;
	TestFalse(TEXT("Front projection failures are not mistaken for behind-camera targets"),
		QuestMarkerProjection::GetBehindCameraDirection(FVector(1, 0, 1), Projection, ViewSize, Direction));
	TestFalse(TEXT("Unavailable viewport cannot produce a marker direction"),
		QuestMarkerProjection::GetBehindCameraDirection(FVector(1, 0, -1), Projection, FVector2D::ZeroVector, Direction));
	TestFalse(TEXT("Nonfinite targets cannot produce a marker direction"),
		QuestMarkerProjection::GetBehindCameraDirection(FVector(std::numeric_limits<double>::infinity(), 0, -1), Projection, ViewSize, Direction));
	return true;
}
#endif
