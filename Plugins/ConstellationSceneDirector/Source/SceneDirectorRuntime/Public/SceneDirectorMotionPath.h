#pragma once
#include "CoreMinimal.h"
#include "Channels/MovieSceneDoubleChannel.h"
#include "SceneDirectorMotionPath.generated.h"
UENUM()
enum class EDirectorPathInterpolation : uint8 { Linear UMETA(DisplayName="직선"), Cubic UMETA(DisplayName="부드럽게"), Constant UMETA(DisplayName="즉시 변경"), Original UMETA(DisplayName="원본 축별 곡선 유지") };
USTRUCT()
struct SCENEDIRECTORRUNTIME_API FDirectorMotionPoint
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere,Category="경유점",meta=(DisplayName="시간 (초)",ClampMin="0")) double Time=0;
    UPROPERTY(EditAnywhere,Category="경유점",meta=(DisplayName="월드 위치 (cm)")) FVector Position=FVector::ZeroVector;
    UPROPERTY(EditAnywhere,Category="경유점",meta=(DisplayName="회전 (Roll, Pitch, Yaw)")) FVector Rotation=FVector::ZeroVector;
    UPROPERTY(EditAnywhere,Category="경유점",meta=(DisplayName="스케일")) FVector Scale=FVector::OneVector;
    UPROPERTY(EditAnywhere,Category="경유점",meta=(DisplayName="다음 점까지 보간")) EDirectorPathInterpolation Interpolation=EDirectorPathInterpolation::Linear;
    UPROPERTY() TArray<FMovieSceneDoubleValue> OriginalValues;
    UPROPERTY() int32 OriginalMask=0;
    UPROPERTY() FVector OriginalPosition=FVector::ZeroVector;
    UPROPERTY() FVector OriginalRotation=FVector::ZeroVector;
    UPROPERTY() FVector OriginalScale=FVector::OneVector;
    double Value(int32 Axis) const {return Axis<3?Position[Axis]:(Axis<6?Rotation[Axis-3]:Scale[Axis-6]);}
    double OriginalValue(int32 Axis) const {return Axis<3?OriginalPosition[Axis]:(Axis<6?OriginalRotation[Axis-3]:OriginalScale[Axis-6]);}
    FTransform Pose() const {return FTransform(FRotator::MakeFromEuler(Rotation),Position,Scale);}
};
struct FDirectorStep;
class UMovieScene3DTransformSection;
namespace DirectorPath
{
    SCENEDIRECTORRUNTIME_API bool Validate(const FDirectorStep& Step,FString& Error);
    SCENEDIRECTORRUNTIME_API void Write(const FDirectorStep& Step,UMovieScene3DTransformSection& Section,int32 Begin);
    SCENEDIRECTORRUNTIME_API FTransform Evaluate(const FDirectorStep& Step,double Seconds);
}
