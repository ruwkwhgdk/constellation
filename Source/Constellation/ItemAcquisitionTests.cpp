#include "ItemAcquisitionSubsystem.h"
#include "Engine/Texture2D.h"
#include "Misc/AutomationTest.h"

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FItemAcquisitionFreshInput,"Constellation.ItemAcquisition.FreshInput",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FItemAcquisitionFreshInput::RunTest(const FString&)
{
 FItemAcquisitionTiming T;T.Reset(true);
 T.Advance(.6f,true);TestFalse(TEXT("Held entering card cannot confirm"),T.Press(false));
 T.Release();TestFalse(TEXT("Repeat cannot confirm"),T.Press(true));
 T.Release();TestTrue(TEXT("Fresh released press confirms"),T.Press(false));
 TestFalse(TEXT("Duplicate press cannot confirm"),T.Press(false));
 T.Advance(1.f,false);TestFalse(TEXT("Inactive app freezes exit"),T.Finished());
 T.Advance(.25f,true);TestTrue(TEXT("Fade completes"),T.Finished());
 T.Reset(false);T.Advance(.2f,true);TestFalse(TEXT("Early press ignored"),T.Press(false));
 T.Advance(.4f,true);TestFalse(TEXT("Early held press still ignored"),T.Press(false));
 T.Release();TestTrue(TEXT("Release then new press accepted"),T.Press(false));
 return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FItemAcquisitionQueue,"Constellation.ItemAcquisition.QueueCancellation",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FItemAcquisitionQueue::RunTest(const FString&)
{
 auto* S=NewObject<UItemAcquisitionSubsystem>();FItemAcquisitionPresentation P;
 TestFalse(TEXT("Missing real payload rejected"),S->Enqueue(P,FKey(),nullptr,{}).IsValid());
 P.Sprite=NewObject<UTexture2D>();P.Name=FText::FromString(TEXT("Test"));P.Description=FText::FromString(TEXT("Test description"));
 int32 A=0,B=0,C=0;
 TestFalse(TEXT("Axis confirmation cannot create an undismissable card"),S->Enqueue(P,EKeys::Gamepad_LeftTriggerAxis,nullptr,{}).IsValid());
 TestFalse(TEXT("Wildcard confirmation rejected"),S->Enqueue(P,EKeys::AnyKey,nullptr,{}).IsValid());
 const FGuid First=S->Enqueue(P,EKeys::F,nullptr,[&](bool Completed){TestFalse(TEXT("Cancelled"),Completed);++A;});
 const FGuid Second=S->Enqueue(P,EKeys::F,nullptr,[&](bool){++B;});
 TestEqual(TEXT("Both queued"),S->PendingCount(),2);
 S->Cancel(Second);S->Cancel(Second);TestEqual(TEXT("Target resolves once"),B,1);TestEqual(TEXT("First preserved"),A,0);
 S->Cancel(First);TestEqual(TEXT("First resolves once"),A,1);
 S->Enqueue(P,EKeys::F,nullptr,[&](bool){++C;S->CancelAll();});S->CancelAll();
 TestEqual(TEXT("Reentrant cancel resolves once"),C,1);TestEqual(TEXT("Queue empty"),S->PendingCount(),0);
 return true;
}
#endif
