#include "SceneDirectorShake.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorPlayer.h"
#include "Camera/PlayerCameraManager.h"
bool FDirectorShakeSettings::Validate(FString& Error) const
{
 auto Bad=[&](){Error=TEXT("카메라 진동: 강도·범위·방향·시간을 확인하세요. 값은 유한해야 하며 음수는 사용할 수 없습니다.");return false;};
 for(double V:{double(Intensity),double(TranslationRange),double(RotationRange),double(Frequency),double(BlendIn),double(BlendOut)})if(!FMath::IsFinite(V)||V<0)return Bad();
 if(Intensity>100||TranslationRange>10000||RotationRange>180||Frequency<=0||Frequency>60||BlendIn>3600||BlendOut>3600)return Bad();
 if(!bUnlimited&&(!FMath::IsFinite(Duration)||Duration<1.f/30.f||Duration>3600))return Bad();
 if(Direction==EDirectorShakeDirection::Custom&&(CustomDirection.ContainsNaN()||CustomDirection.IsNearlyZero()))return Bad();
 if(uint8(Direction)>uint8(EDirectorShakeDirection::Custom))return Bad();
 return true;
}
void FDirectorShakeOffset::Apply(FVector& Position,FRotator& Orientation) const
{
 Position+=Orientation.Quaternion().RotateVector(Location);
 Orientation=(Orientation.Quaternion()*Rotation.Quaternion()).Rotator();
}
float FDirectorShakeState::FActive::Weight() const
{
 float W=Settings.BlendIn>0?FMath::Clamp(float(Age/Settings.BlendIn),0.f,1.f):1;
 if(!Settings.bUnlimited)
 {
  if(Age>=Settings.Duration)return 0;
  if(Settings.BlendOut>0)W=FMath::Min(W,FMath::Clamp(float((Settings.Duration-Age)/Settings.BlendOut),0.f,1.f));
 }
 if(StopAge>=0)W=FMath::Min(W,StopSeconds>0?StopWeight*FMath::Clamp(float(1-(Age-StopAge)/StopSeconds),0.f,1.f):0);
 return W;
}
void FDirectorShakeState::Execute(const FDirectorStep& S)
{
 const FName Key=S.bShakeCurrentCamera?NAME_None:S.CameraKey;
 if(S.Type==EDirectorNodeType::CameraShake)
 {
  FActive A;A.Settings=S.Shake;A.Seed=GetTypeHash(S.Id);Active.Add(Key,A);
 }
 else if(S.Type==EDirectorNodeType::StopCameraShake)
 {
  for(auto It=Active.CreateIterator();It;++It)if(S.bStopAllCameraShakes||It.Key()==Key)
  {
   if(S.StopShakeSeconds<=0)It.RemoveCurrent();
   else if(It.Value().StopAge<0){auto& A=It.Value();A.StopWeight=A.Weight();A.StopAge=A.Age;A.StopSeconds=S.StopShakeSeconds;}
  }
 }
}
void FDirectorShakeState::Advance(double Seconds)
{
 if(!FMath::IsFinite(Seconds)||Seconds<0)return;
 for(auto It=Active.CreateIterator();It;++It)
 {
  auto& A=It.Value();A.Age+=Seconds;
  if((!A.Settings.bUnlimited&&A.Age>=A.Settings.Duration)||(A.StopAge>=0&&A.Age>=A.StopAge+A.StopSeconds))It.RemoveCurrent();
 }
}
FDirectorShakeOffset FDirectorShakeState::Sample(FName CameraKey) const
{
 FDirectorShakeOffset Out;
 for(const auto& Pair:Active)
 {
  if(!Pair.Key.IsNone()&&Pair.Key!=CameraKey)continue;
  const auto& A=Pair.Value;const auto& S=A.Settings;
  // Bounded deterministic waveform. Combined movement never exceeds the specified radius.
  const double Phase=A.Age*S.Frequency*2*PI+(A.Seed%1009)*.013;
  FVector D;
  switch(S.Direction)
  {
  case EDirectorShakeDirection::Vertical:D=FVector(0,0,FMath::Sin(Phase));break;
  case EDirectorShakeDirection::Horizontal:D=FVector(0,FMath::Sin(Phase),0);break;
  case EDirectorShakeDirection::Forward:D=FVector(FMath::Sin(Phase),0,0);break;
  case EDirectorShakeDirection::Custom:D=S.CustomDirection.GetSafeNormal()*FMath::Sin(Phase);break;
  default:D=FVector(FMath::Sin(Phase*.83),FMath::Sin(Phase*1.13+1),FMath::Sin(Phase+2))/FMath::Sqrt(3.);break;
  }
  const float Gain=S.Intensity*A.Weight();
  Out.Location+=D*(S.TranslationRange*Gain);
  // Vertical -> pitch, horizontal -> yaw, forward -> roll.
  Out.Rotation+=FRotator(D.Z*S.RotationRange*Gain,D.Y*S.RotationRange*Gain,D.X*S.RotationRange*Gain);
 }
 return Out;
}
FDirectorShakeState FDirectorShakeState::At(const TArray<FDirectorCue>& Cues,double Seconds)
{
 FDirectorShakeState State;TArray<const FDirectorCue*> Ordered;
 for(const auto& C:Cues)if(C.Step.Type==EDirectorNodeType::CameraShake||C.Step.Type==EDirectorNodeType::StopCameraShake)Ordered.Add(&C);
 Ordered.StableSort([](const FDirectorCue& A,const FDirectorCue& B){return A.StartFrame<B.StartFrame;});
 double Previous=0;
 for(const auto* C:Ordered)
 {
  const double Start=C->StartFrame/30.;if(Start>Seconds)break;
  State.Advance(Start-Previous);State.Execute(C->Step);Previous=Start;
 }
 State.Advance(FMath::Max(0.,Seconds-Previous));return State;
}
bool UDirectorCameraShakeModifier::ModifyCamera(float DeltaTime,FMinimalViewInfo& POV)
{
 if(DirectorPlayer.IsValid()&&CameraOwner)
 {
  auto Offset=DirectorPlayer->GetCameraShake(CameraOwner->GetViewTarget());
  Offset.Apply(POV.Location,POV.Rotation);
 }
 return false;
}
