#include "SceneDirectorMotionPath.h"
#include "SceneDirectorAsset.h"
#include "Sections/MovieScene3DTransformSection.h"
namespace DirectorPath
{
bool Validate(const FDirectorStep& S,FString& Error)
{
    if(!S.bUseMotionPath)return true;
    if(S.MotionPoints.Num()<2){Error=TEXT("경유점은 시작점(0초)을 포함하여 2개 이상 필요합니다.");return false;}
    double Last=-1;
    for(const auto& P:S.MotionPoints)
    {
        if(!FMath::IsFinite(P.Time)||P.Time<0||P.Time>3600||P.Time<=Last||!FMath::IsNearlyEqual(P.Time*30,FMath::RoundToDouble(P.Time*30),.0001)||!P.Pose().IsValid()||P.Scale.GetAbsMin()<KINDA_SMALL_NUMBER||uint8(P.Interpolation)>uint8(EDirectorPathInterpolation::Original))
        {Error=TEXT("경유점 시간은 30fps 프레임에 맞춰 오름차순으로 입력하고 위치·회전·스케일을 확인하세요.");return false;}
        if(P.Interpolation==EDirectorPathInterpolation::Original&&P.OriginalValues.Num()!=9){Error=TEXT("새 경유점은 직선/부드럽게/즉시 변경 중에서 보간을 선택하세요.");return false;}
        for(const auto& V:P.OriginalValues)if(!FMath::IsFinite(V.Value)||!FMath::IsFinite(V.Tangent.ArriveTangent)||!FMath::IsFinite(V.Tangent.LeaveTangent)||!FMath::IsFinite(V.Tangent.ArriveTangentWeight)||!FMath::IsFinite(V.Tangent.LeaveTangentWeight)){Error=TEXT("원본 커브의 탄젠트 값이 유효하지 않습니다.");return false;}
        Last=P.Time;
    }
    if(!FMath::IsNearlyZero(S.MotionPoints[0].Time)){Error=TEXT("첫 경유점 시간은 0초여야 합니다.");return false;}
    return true;
}
void Write(const FDirectorStep& S,UMovieScene3DTransformSection& Section,int32 Begin)
{
    auto Channels=Section.GetChannelProxy().GetChannels<FMovieSceneDoubleChannel>();
    for(int32 Axis=0;Axis<9;++Axis)
    {
        Channels[Axis]->SetTickResolution(FFrameRate(30,1));
        TArray<FFrameNumber> Times;TArray<FMovieSceneDoubleValue> Values;
        for(const auto& P:S.MotionPoints)
        {
            FMovieSceneDoubleValue V(P.Value(Axis));
            if(P.Interpolation==EDirectorPathInterpolation::Original)
            {
                if(!(P.OriginalMask&(1<<Axis))&&P.Value(Axis)==P.OriginalValue(Axis))continue;
                V=P.OriginalValues[Axis];V.Value=P.Value(Axis);
            }
            else {V.InterpMode=P.Interpolation==EDirectorPathInterpolation::Cubic?RCIM_Cubic:(P.Interpolation==EDirectorPathInterpolation::Constant?RCIM_Constant:RCIM_Linear);V.TangentMode=RCTM_Auto;}
            Times.Add(FFrameNumber(Begin+int32(FMath::RoundToInt(P.Time*30))));Values.Add(V);
        }
        Channels[Axis]->GetData().UpdateOrAddKeys(Times,Values);
        // Only authored cubic keys get auto tangents; original tangent data remains untouched.
        if(S.MotionPoints.ContainsByPredicate([](const FDirectorMotionPoint& P){return P.Interpolation==EDirectorPathInterpolation::Cubic;})){
            Channels[Axis]->AutoSetTangents();
            for(const auto& P:S.MotionPoints)if(P.Interpolation==EDirectorPathInterpolation::Original)
            {auto Data=Channels[Axis]->GetData();int32 Index=Data.GetTimes().Find(FFrameNumber(Begin+int32(FMath::RoundToInt(P.Time*30))));if(Index!=INDEX_NONE){auto V=P.OriginalValues[Axis];V.Value=P.Value(Axis);Data.GetValues()[Index]=V;}}
        }
    }
}
FTransform Evaluate(const FDirectorStep& S,double Seconds)
{
    auto* Section=NewObject<UMovieScene3DTransformSection>();Write(S,*Section,0);auto C=Section->GetChannelProxy().GetChannels<FMovieSceneDoubleChannel>();
    FVector P=S.MotionPoints[0].Position,R=S.MotionPoints[0].Rotation,Z=S.MotionPoints[0].Scale;
    for(int32 I=0;I<3;++I){C[I]->Evaluate(FFrameTime::FromDecimal(Seconds*30),P[I]);C[I+3]->Evaluate(FFrameTime::FromDecimal(Seconds*30),R[I]);C[I+6]->Evaluate(FFrameTime::FromDecimal(Seconds*30),Z[I]);}
    return FTransform(FRotator::MakeFromEuler(R),P,Z);
}
}
