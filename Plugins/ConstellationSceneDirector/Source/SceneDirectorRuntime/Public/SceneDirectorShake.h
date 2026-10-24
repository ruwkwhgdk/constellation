#pragma once
#include "CoreMinimal.h"
#include "Camera/CameraModifier.h"
#include "SceneDirectorShake.generated.h"
UENUM(BlueprintType)
enum class EDirectorShakeDirection:uint8 { Vertical UMETA(DisplayName="상하"), Horizontal UMETA(DisplayName="좌우"), Forward UMETA(DisplayName="앞뒤"), Combined UMETA(DisplayName="복합"), Custom UMETA(DisplayName="직접 지정") };
USTRUCT(BlueprintType)
struct SCENEDIRECTORRUNTIME_API FDirectorShakeSettings
{
 GENERATED_BODY()
 UPROPERTY(EditAnywhere,Category="진동",meta=(DisplayName="무제한",ToolTip="다음 노드로 즉시 진행합니다. 진동 중단 노드 또는 연출 종료까지 유지됩니다.")) bool bUnlimited=false;
 UPROPERTY(EditAnywhere,Category="진동",meta=(DisplayName="지속 시간 (초)",ClampMin="0.033334",EditCondition="!bUnlimited",EditConditionHides)) float Duration=1;
 UPROPERTY(EditAnywhere,Category="진동",meta=(DisplayName="강도 배율",ClampMin="0",ClampMax="100")) float Intensity=1;
 UPROPERTY(EditAnywhere,Category="진동",meta=(DisplayName="최대 이동 범위 (cm)",ClampMin="0",ClampMax="10000")) float TranslationRange=3;
 UPROPERTY(EditAnywhere,Category="진동",meta=(DisplayName="최대 회전 범위 (도)",ClampMin="0",ClampMax="180")) float RotationRange=1;
 UPROPERTY(EditAnywhere,Category="진동",meta=(DisplayName="방향 (카메라 기준)")) EDirectorShakeDirection Direction=EDirectorShakeDirection::Combined;
 UPROPERTY(EditAnywhere,Category="진동",meta=(DisplayName="방향 벡터 (X=앞뒤, Y=좌우, Z=상하)",EditCondition="Direction == EDirectorShakeDirection::Custom",EditConditionHides)) FVector CustomDirection=FVector(0,0,1);
 UPROPERTY(EditAnywhere,Category="진동",meta=(DisplayName="진동 속도 (Hz)",ClampMin="0.01",ClampMax="60")) float Frequency=8;
 UPROPERTY(EditAnywhere,Category="진동",meta=(DisplayName="시작 완화 (초)",ClampMin="0",ClampMax="3600")) float BlendIn=.15f;
 UPROPERTY(EditAnywhere,Category="진동",meta=(DisplayName="종료 완화 (초)",ClampMin="0",ClampMax="3600",EditCondition="!bUnlimited",EditConditionHides)) float BlendOut=.2f;
 bool Validate(FString& Error) const;
};
struct FDirectorCue;
struct FDirectorStep;
struct SCENEDIRECTORRUNTIME_API FDirectorShakeOffset
{
 FVector Location=FVector::ZeroVector;
 FRotator Rotation=FRotator::ZeroRotator;
 void Apply(FVector& Position,FRotator& Orientation) const;
};
// A separate layer: never writes the camera actor or its Sequencer transform.
class SCENEDIRECTORRUNTIME_API FDirectorShakeState
{
 struct FActive
 {
  FDirectorShakeSettings Settings;
  double Age=0,StopAge=-1;
  float StopSeconds=0,StopWeight=1;
  uint32 Seed=0;
  float Weight() const;
 };
 TMap<FName,FActive> Active;
public:
 void Execute(const FDirectorStep& Step);
 void Advance(double Seconds);
 void Reset(){Active.Reset();}
 int32 Num()const{return Active.Num();}
 FDirectorShakeOffset Sample(FName CameraKey) const;
 static FDirectorShakeState At(const TArray<FDirectorCue>& Cues,double Seconds);
};
class ASceneDirectorPlayer;
UCLASS()
class SCENEDIRECTORRUNTIME_API UDirectorCameraShakeModifier:public UCameraModifier
{
 GENERATED_BODY()
public:
 TWeakObjectPtr<ASceneDirectorPlayer> DirectorPlayer;
 virtual bool ModifyCamera(float DeltaTime,FMinimalViewInfo& POV) override;
};
