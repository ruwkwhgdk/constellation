#include "SceneDirectorVision.h"
#include "SceneDirectorNodeTypes.h"
namespace
{
 bool Unit(float V){return FMath::IsFinite(V)&&V>=0&&V<=1;}
 bool Time(float V){return FMath::IsFinite(V)&&V>=0;}
 float Alpha(double T,double D,EDirectorVisionCurve Curve)
 {
  float A=D<=0?1.f:FMath::Clamp(float(T/D),0.f,1.f);
  return Curve==EDirectorVisionCurve::Smooth?A*A*(3-2*A):A;
 }
 float EyeAt(const FDirectorStep& S,double T)
 {
  float Open=S.EyeFrom;T-=S.EyeStartHold;if(T<0)return Open;
  if(S.EyeMode==EDirectorEyeMode::Blink)for(const auto& B:S.Blinks)
  {
   if(T<B.OpenSeconds)return FMath::Lerp(Open,B.OpenAmount,Alpha(T,B.OpenSeconds,S.VisionCurve));
   T-=B.OpenSeconds;if(T<B.OpenHold)return B.OpenAmount;T-=B.OpenHold;
   if(T<B.CloseSeconds)return FMath::Lerp(B.OpenAmount,0.f,Alpha(T,B.CloseSeconds,S.VisionCurve));
   T-=B.CloseSeconds;if(T<B.ClosedHold)return 0;T-=B.ClosedHold;Open=0;
  }
  float Goal=S.EyeMode==EDirectorEyeMode::Open?1.f:(S.EyeMode==EDirectorEyeMode::Close?0.f:S.EyeFinalOpen);
  return FMath::Lerp(Open,Goal,Alpha(T,S.EyeFinalSeconds,S.VisionCurve));
 }
}
bool DirectorVision::Validate(const FDirectorStep& S,FString& Error)
{
 auto Fail=[&](){Error=TEXT("눈꺼풀/시야 효과: 강도는 0~1, 시간은 유한한 양수, 깜박임은 1~8회로 지정하세요.");return false;};
 if(S.VisionCurve!=EDirectorVisionCurve::Linear&&S.VisionCurve!=EDirectorVisionCurve::Smooth)return Fail();
 if(S.Type==EDirectorNodeType::Eyelids)
 {
  if(S.EyeMode!=EDirectorEyeMode::Open&&S.EyeMode!=EDirectorEyeMode::Close&&S.EyeMode!=EDirectorEyeMode::Blink)return Fail();
  if(!Unit(S.EyeFrom)||!Unit(S.EyeFinalOpen)||!Time(S.EyeStartHold)||!Time(S.EyeFinalHold)||!Time(S.EyeFinalSeconds)||S.EyeFinalSeconds<1.f/30)return Fail();
  if(S.EyeMode==EDirectorEyeMode::Blink)
  {
   if(S.Blinks.Num()<1||S.Blinks.Num()>8)return Fail();
   for(const auto& B:S.Blinks)if(!Unit(B.OpenAmount)||!Time(B.OpenSeconds)||B.OpenSeconds<1.f/30||!Time(B.CloseSeconds)||B.CloseSeconds<1.f/30||!Time(B.OpenHold)||!Time(B.ClosedHold))return Fail();
  }
 }
 else if(S.Type==EDirectorNodeType::Vision)
 {
  if(!Unit(S.BlurFrom)||!Unit(S.BlurTo)||!Unit(S.HazeFrom)||!Unit(S.HazeTo)||!Unit(S.HazeColor.R)||!Unit(S.HazeColor.G)||!Unit(S.HazeColor.B))return Fail();
  if(!Time(S.Duration)||S.Duration<1.f/30)return Fail();
 }
 else if(S.Type==EDirectorNodeType::ClearVision&&!S.bClearVisionInstant&&(!Time(S.Duration)||S.Duration<1.f/30))return Fail();
 if(Duration(S)>3600)return Fail();
 return true;
}
double DirectorVision::Duration(const FDirectorStep& S)
{
 if(S.Type==EDirectorNodeType::ClearVision)return S.bClearVisionInstant?0:S.Duration;
 if(S.Type!=EDirectorNodeType::Eyelids)return S.Duration;
 double T=double(S.EyeStartHold)+S.EyeFinalSeconds+S.EyeFinalHold;
 if(S.EyeMode==EDirectorEyeMode::Blink)for(const auto& B:S.Blinks)T+=double(B.OpenSeconds)+B.OpenHold+B.CloseSeconds+B.ClosedHold;
 return T;
}
bool DirectorVision::Conflicts(EDirectorNodeType A,EDirectorNodeType B)
{
 return DirectorNodes::IsScreenEffect(A)&&DirectorNodes::IsScreenEffect(B)&&(A==B||A==EDirectorNodeType::ClearVision||B==EDirectorNodeType::ClearVision);
}
FDirectorVisionState DirectorVision::Evaluate(const TArray<FDirectorCue>& Cues,double Frame)
{
 TArray<const FDirectorCue*> Sorted;
 for(const auto& C:Cues)if(C.StartFrame<=Frame&&DirectorNodes::IsScreenEffect(C.Step.Type))Sorted.Add(&C);
 Sorted.StableSort([](const FDirectorCue& A,const FDirectorCue& B){return A.StartFrame<B.StartFrame;});
 FDirectorVisionState State;const FDirectorCue* Eyes=nullptr;const FDirectorCue* Vision=nullptr;
 FDirectorVisionState ResetStart;const FDirectorCue* Reset=nullptr;
 auto Sample=[&](double At)
 {
  FDirectorVisionState Result=State;
  if(Reset){float A=Alpha((At-Reset->StartFrame)/30.,Duration(Reset->Step),Reset->Step.VisionCurve);Result.EyeOpen=FMath::Lerp(ResetStart.EyeOpen,1.f,A);Result.Blur=ResetStart.Blur*(1-A);Result.Haze=ResetStart.Haze*(1-A);}
  if(Eyes)Result.EyeOpen=EyeAt(Eyes->Step,(At-Eyes->StartFrame)/30.);
  if(Vision){const auto& S=Vision->Step;float A=Alpha((At-Vision->StartFrame)/30.,Duration(S),S.VisionCurve);Result.Blur=FMath::Lerp(S.BlurFrom,S.BlurTo,A);Result.Haze=FMath::Lerp(S.HazeFrom,S.HazeTo,A);Result.HazeColor=S.HazeColor;}
  return Result;
 };
 for(const auto* C:Sorted)
 {
  if(C->Step.Type==EDirectorNodeType::ClearVision){State=Sample(C->StartFrame);ResetStart=State;Reset=C;Eyes=Vision=nullptr;}
  else if(C->Step.Type==EDirectorNodeType::Eyelids)Eyes=C;
  else Vision=C;
 }
 return Sample(Frame);
}
