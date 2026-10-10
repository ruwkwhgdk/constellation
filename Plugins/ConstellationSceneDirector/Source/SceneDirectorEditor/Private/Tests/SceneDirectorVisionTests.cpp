#include "Misc/AutomationTest.h"
#include "SceneDirectorAsset.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorVisionContractTest,"Constellation.SceneDirector.Vision.Contract",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorVisionContractTest::RunTest(const FString&)
{
 auto* E=StaticEnum<EDirectorNodeType>();
 for(const TCHAR* Name:{TEXT("Eyelids"),TEXT("Vision"),TEXT("ClearVision")})TestTrue(Name,E->GetIndexByNameString(Name)!=INDEX_NONE);
 return true;
}

#include "SceneDirectorVision.h"
#include "SceneDirectorCompiler.h"
#include "SceneDirectorPlayer.h"
#include "Engine/World.h"
namespace
{
 FDirectorStep WakeEyes()
 {
  FDirectorStep S;S.Type=EDirectorNodeType::Eyelids;S.Blinks.SetNum(2);
  S.Blinks[1].OpenAmount=.65f;S.Blinks[1].OpenSeconds=.5f;S.Blinks[1].OpenHold=.2f;S.Blinks[1].CloseSeconds=.14f;
  return S;
 }
 FDirectorCue Cue(FDirectorStep S,int32 Start=0){FDirectorCue C;C.Step=S;C.StartFrame=Start;C.EndFrame=Start+FMath::RoundToInt(DirectorVision::Duration(S)*30);return C;}
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorVisionSamplingTest,"Constellation.SceneDirector.Vision.Sampling",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorVisionSamplingTest::RunTest(const FString&)
{
 auto E=WakeEyes();FDirectorStep V;V.Type=EDirectorNodeType::Vision;V.Duration=4;
 TArray<FDirectorCue> C={Cue(E),Cue(V)};
 TestTrue(TEXT("four second eye performance"),FMath::IsNearlyEqual(DirectorVision::Duration(E),4.,.00001));
 TestEqual(TEXT("starts closed"),DirectorVision::Evaluate(C,0).EyeOpen,0.f);
 TestTrue(TEXT("starts blurred"),DirectorVision::Evaluate(C,0).Blur>.7f);
 TestTrue(TEXT("first partial opening"),FMath::IsNearlyEqual(DirectorVision::Evaluate(C,.84*30).EyeOpen,.3f,.001f));
 TestTrue(TEXT("first closure"),DirectorVision::Evaluate(C,1.08*30).EyeOpen<.001f);
 TestTrue(TEXT("second partial opening"),FMath::IsNearlyEqual(DirectorVision::Evaluate(C,1.65*30).EyeOpen,.65f,.001f));
 TestTrue(TEXT("second closure"),DirectorVision::Evaluate(C,1.98*30).EyeOpen<.001f);
 auto Done=DirectorVision::Evaluate(C,4*30);TestEqual(TEXT("ends fully open"),Done.EyeOpen,1.f);TestEqual(TEXT("clear blur"),Done.Blur,0.f);TestEqual(TEXT("clear haze"),Done.Haze,0.f);
 auto Back=DirectorVision::Evaluate(C,.84*30);TestTrue(TEXT("reverse seek reproduces first opening"),FMath::IsNearlyEqual(Back.EyeOpen,.3f,.001f));
 FDirectorStep Clear;Clear.Type=EDirectorNodeType::ClearVision;Clear.bClearVisionInstant=false;Clear.Duration=1;C.Add(Cue(Clear,15));
 auto Before=DirectorVision::Evaluate({Cue(E),Cue(V)},15);auto Middle=DirectorVision::Evaluate(C,30);
 TestTrue(TEXT("reset blends from sampled state"),FMath::IsNearlyEqual(Middle.Blur,Before.Blur*.5f,.001f));
 Done=DirectorVision::Evaluate(C,60);TestEqual(TEXT("reset removes eyelids"),Done.EyeOpen,1.f);TestEqual(TEXT("reset removes blur"),Done.Blur,0.f);
 C.Last().Step.bClearVisionInstant=true;TestEqual(TEXT("instant reset"),DirectorVision::Evaluate(C,15).EyeOpen,1.f);
 return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorVisionScheduleTest,"Constellation.SceneDirector.Vision.Schedule",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorVisionScheduleTest::RunTest(const FString&)
{
 auto* A=NewObject<USceneDirectorAsset>();A->Steps.SetNum(5);auto& S=A->Steps;S[0].Type=EDirectorNodeType::Start;S[1]=WakeEyes();S[1].bWaitForCompletion=false;
 S[2].Type=EDirectorNodeType::Vision;S[2].Duration=4;S[3].Type=EDirectorNodeType::Hub;S[4].Type=EDirectorNodeType::End;
 for(int I=0;I<4;++I)S[I].NextNodes={S[I+1].Id};
 FDirectorSchedule Plan;FString Error;if(!TestTrue(TEXT("parallel distinct channels compile"),FSceneDirectorCompiler::Schedule(*A,Plan,Error))){AddError(Error);return false;}
 TestEqual(TEXT("same start"),Plan.StartFrames[1],Plan.StartFrames[2]);TestEqual(TEXT("join waits for full performance"),Plan.StartFrames[3],120);
 S[2]=WakeEyes();S[1].NextNodes={S[2].Id};S[2].NextNodes={S[3].Id};TestFalse(TEXT("overlapping eyelids rejected"),FSceneDirectorCompiler::Schedule(*A,Plan,Error));
 S[2].Type=EDirectorNodeType::ClearVision;S[2].bClearVisionInstant=true;TestFalse(TEXT("instant reset cannot race an active writer"),FSceneDirectorCompiler::Schedule(*A,Plan,Error));
 S[1].Type=EDirectorNodeType::ClearVision;S[1].bClearVisionInstant=true;S[2]=WakeEyes();S[1].NextNodes={S[2].Id};S[2].NextNodes={S[3].Id};
 TestTrue(TEXT("instant reset before same-frame eyelids is ordered"),FSceneDirectorCompiler::Schedule(*A,Plan,Error));
 S[2].Type=EDirectorNodeType::Vision;TestTrue(TEXT("instant reset before same-frame vision is ordered"),FSceneDirectorCompiler::Schedule(*A,Plan,Error));
 auto Invalid=WakeEyes();Invalid.Blinks[0].CloseSeconds=-1;TestFalse(TEXT("negative duration rejected"),DirectorVision::Validate(Invalid,Error));
 Invalid=WakeEyes();Invalid.Blinks.Reset();
 TestFalse(TEXT("empty blink list rejected"),DirectorVision::Validate(Invalid,Error));
 Invalid=WakeEyes();Invalid.EyeFrom=2;TestFalse(TEXT("out of range opening rejected"),DirectorVision::Validate(Invalid,Error));
 auto* W=UWorld::CreateWorld(EWorldType::Game,false);auto* P=W->SpawnActor<ASceneDirectorPlayer>();P->StopDirector();TestFalse(TEXT("stop idempotently removes overlay"),P->HasVisionOverlay());TestEqual(TEXT("stop resets sampled eyes"),P->GetEyeOpen(),1.f);W->DestroyWorld(false);
 return true;
}
