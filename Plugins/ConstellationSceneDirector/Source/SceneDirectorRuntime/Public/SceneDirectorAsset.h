#pragma once
#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "SceneDirectorCharacterProfile.h"
#include "SceneDirectorChoice.h"
#include "SceneDirectorAction.h"
#include "SceneDirectorSequence.h"
#include "SceneDirectorMotionPath.h"
#include "Generators/MovieSceneEasingCurves.h"
#include "SceneDirectorSpeaker.h"
#include "SceneDirectorAsset.generated.h"

class ULevelSequence;
class UAnimSequence;
class USoundBase;
UENUM(BlueprintType)
enum class EDirectorNodeType : uint8 { Start, SpawnNPC, Camera, Wait, End, Animation, Hub, CharacterMove, CameraMove, BindNPC, CinematicMode, CameraPreset, LookAt, Expression, Dialogue, CameraSwitch, GameplayReturn, Condition, SetBool, GameAction, Sequence, Visibility, Fade, SetInt, PlayerHidden, InputLock, HUDHidden, CameraReturn, CloseDialogue };

UENUM(BlueprintType)
enum class EDirectorValueMode : uint8 { Absolute UMETA(DisplayName="절대값"), Key UMETA(DisplayName="String Key"), Current UMETA(DisplayName="현재 값") };
UENUM(BlueprintType)
enum class EDirectorMoveTiming : uint8 { Speed UMETA(DisplayName="속도 기준"), Duration UMETA(DisplayName="시간 기준") };
UENUM(BlueprintType)
enum class EDirectorActorSource : uint8 { Player UMETA(DisplayName="플레이어"), Tag UMETA(DisplayName="레벨 Actor 태그"), Object UMETA(DisplayName="등록 오브젝트 Key") };
UENUM(BlueprintType)
enum class EDirectorFraming : uint8 { CloseUp UMETA(DisplayName="얼굴 클로즈업"), Medium UMETA(DisplayName="상반신"), Full UMETA(DisplayName="전신"), OverShoulder UMETA(DisplayName="오버숄더") };
UENUM(BlueprintType)
enum class EDirectorDialogueAdvance : uint8 { Timed UMETA(DisplayName="지정 시간 후"), Voice UMETA(DisplayName="음성 종료 후"), Click UMETA(DisplayName="시간/음성 종료 후 클릭") };
USTRUCT(BlueprintType)
struct SCENEDIRECTORRUNTIME_API FDirectorVectorInput
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere,Category="입력",meta=(DisplayName="입력 방식")) EDirectorValueMode Mode=EDirectorValueMode::Absolute;
    UPROPERTY(EditAnywhere,Category="입력",meta=(DisplayName="Vector3",EditCondition="Mode == EDirectorValueMode::Absolute",EditConditionHides)) FVector Value=FVector::ZeroVector;
    UPROPERTY(EditAnywhere,Category="입력",meta=(DisplayName="Vector3 String Key",EditCondition="Mode == EDirectorValueMode::Key",EditConditionHides)) FName Key;
    UPROPERTY(EditAnywhere,Category="입력",meta=(DisplayName="Offset",EditCondition="Mode == EDirectorValueMode::Key || Mode == EDirectorValueMode::Current",EditConditionHides)) FVector Offset=FVector::ZeroVector;
    UPROPERTY(EditAnywhere,Category="입력",meta=(DisplayName="현재 위치/회전에 더하기",EditCondition="Mode == EDirectorValueMode::Key",EditConditionHides)) bool bAddCurrent=false;
};
USTRUCT(BlueprintType)
struct SCENEDIRECTORRUNTIME_API FDirectorCameraEntry
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere,Category="카메라",meta=(DisplayName="기존 오브젝트 Key (선택)")) FName ObjectKey;
    UPROPERTY(Instanced) TObjectPtr<AActor> ImportedTemplate;
    UPROPERTY(meta=(IgnoreForMemberInitializationTest)) FGuid Id=FGuid::NewGuid();
    UPROPERTY(EditAnywhere,Category="카메라",meta=(DisplayName="String Key")) FName Key;
    UPROPERTY(EditAnywhere,Category="카메라",meta=(DisplayName="초기 위치·회전")) FTransform Transform;
    UPROPERTY(EditAnywhere,Category="카메라",meta=(DisplayName="화각",ClampMin="10",ClampMax="170")) float FieldOfView=50;
};
USTRUCT(BlueprintType)
struct SCENEDIRECTORRUNTIME_API FDirectorObjectEntry
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere,Category="오브젝트",meta=(DisplayName="String Key")) FName Key;
    UPROPERTY(EditAnywhere,Category="오브젝트",meta=(DisplayName="대상 클래스")) TSubclassOf<AActor> ActorClass;
    UPROPERTY(EditAnywhere,Category="오브젝트",meta=(DisplayName="기본 Actor 태그")) FName ActorTag;
};
USTRUCT(BlueprintType)
struct SCENEDIRECTORRUNTIME_API FDirectorVectorEntry
{
    GENERATED_BODY()
    UPROPERTY(meta=(IgnoreForMemberInitializationTest)) FGuid Id=FGuid::NewGuid();
    UPROPERTY(EditAnywhere,Category="Vector3",meta=(DisplayName="String Key")) FName Key;
    UPROPERTY(EditAnywhere,Category="Vector3",meta=(DisplayName="Vector3 값")) FVector Value=FVector::ZeroVector;
};
USTRUCT(BlueprintType)
struct SCENEDIRECTORRUNTIME_API FDirectorBoolEntry
{
    GENERATED_BODY()
    UPROPERTY(meta=(IgnoreForMemberInitializationTest)) FGuid Id=FGuid::NewGuid();
    UPROPERTY(EditAnywhere,Category="조건 변수",meta=(DisplayName="String Key")) FName Key;
    UPROPERTY(EditAnywhere,Category="조건 변수",meta=(DisplayName="초기값")) bool Value=false;
};
UENUM(BlueprintType)
enum class EDirectorDialoguePosition:uint8 { Top UMETA(DisplayName="상단"), Center UMETA(DisplayName="중단"), Bottom UMETA(DisplayName="하단") };
UENUM(BlueprintType)
enum class EDirectorVariableType:uint8 { Boolean, Integer };
UENUM(BlueprintType)
enum class EDirectorComparison:uint8 { Equal UMETA(DisplayName="같음"), NotEqual UMETA(DisplayName="다름"), Greater UMETA(DisplayName="초과"), GreaterEqual UMETA(DisplayName="이상"), Less UMETA(DisplayName="미만"), LessEqual UMETA(DisplayName="이하") };
USTRUCT(BlueprintType)
struct SCENEDIRECTORRUNTIME_API FDirectorIntEntry
{
 GENERATED_BODY()
 UPROPERTY(EditAnywhere,Category="변수",meta=(DisplayName="String Key")) FName Key;
 UPROPERTY(EditAnywhere,Category="변수",meta=(DisplayName="초기값")) int32 Value=0;
};
USTRUCT(BlueprintType)
struct SCENEDIRECTORRUNTIME_API FDirectorVariableEntry
{
 GENERATED_BODY()
 UPROPERTY(meta=(IgnoreForMemberInitializationTest)) FGuid Id=FGuid::NewGuid();
 UPROPERTY(EditAnywhere,Category="변수",meta=(DisplayName="이름")) FName Key;
 UPROPERTY(EditAnywhere,Category="변수",meta=(DisplayName="타입")) EDirectorVariableType Type=EDirectorVariableType::Boolean;
 UPROPERTY(EditAnywhere,Category="변수",meta=(DisplayName="초기값",EditCondition="Type == EDirectorVariableType::Boolean",EditConditionHides)) bool BoolValue=false;
 UPROPERTY(EditAnywhere,Category="변수",meta=(DisplayName="초기값",EditCondition="Type == EDirectorVariableType::Integer",EditConditionHides)) int32 IntValue=0;
};
USTRUCT(BlueprintType)
struct SCENEDIRECTORRUNTIME_API FDirectorEventCondition
{
 GENERATED_BODY()
 UPROPERTY(EditAnywhere,Category="실행 조건",meta=(DisplayName="변수 종류")) EDirectorVariableType Type=EDirectorVariableType::Boolean;
 UPROPERTY(EditAnywhere,Category="실행 조건",meta=(DisplayName="변수 Key")) FName Key;
 UPROPERTY(EditAnywhere,Category="실행 조건",meta=(DisplayName="Boolean 값",EditCondition="Type == EDirectorVariableType::Boolean",EditConditionHides)) bool BoolValue=true;
 UPROPERTY(EditAnywhere,Category="실행 조건",meta=(DisplayName="비교",EditCondition="Type == EDirectorVariableType::Integer",EditConditionHides)) EDirectorComparison Comparison=EDirectorComparison::Equal;
 UPROPERTY(EditAnywhere,Category="실행 조건",meta=(DisplayName="Integer 값",EditCondition="Type == EDirectorVariableType::Integer",EditConditionHides)) int32 IntValue=0;
};
USTRUCT(BlueprintType)
struct SCENEDIRECTORRUNTIME_API FDirectorActionEntry
{
    GENERATED_BODY()
    UPROPERTY(meta=(IgnoreForMemberInitializationTest)) FGuid Id=FGuid::NewGuid();
    UPROPERTY(EditAnywhere,Category="액션",meta=(DisplayName="String Key")) FName Key;
    UPROPERTY(EditAnywhere,Category="액션",meta=(DisplayName="액션 BP",AllowAbstract="false")) TSubclassOf<USceneDirectorAction> ActionClass;
};
USTRUCT(BlueprintType)
struct SCENEDIRECTORRUNTIME_API FDirectorStep
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere,Category="대사",meta=(DisplayName="대사창 유지",EditCondition="Type == EDirectorNodeType::Dialogue",EditConditionHides)) bool bKeepDialogueOpen=true;
    UPROPERTY(EditAnywhere,Category="대사",meta=(DisplayName="화면 위치",EditCondition="Type == EDirectorNodeType::Dialogue",EditConditionHides)) EDirectorDialoguePosition DialoguePosition=EDirectorDialoguePosition::Bottom;
    UPROPERTY(EditAnywhere,Category="Integer 변수",meta=(DisplayName="변수 Key",EditCondition="Type == EDirectorNodeType::SetInt",EditConditionHides)) FName IntKey;
    UPROPERTY(EditAnywhere,Category="Integer 변수",meta=(DisplayName="설정 값",EditCondition="Type == EDirectorNodeType::SetInt",EditConditionHides)) int32 IntValue=0;
    UPROPERTY(meta=(IgnoreForMemberInitializationTest)) FGuid Id = FGuid::NewGuid();
    // Kept for loading version 1 assets.
    UPROPERTY(EditAnywhere,Category="기존 오브젝트",meta=(DisplayName="오브젝트 Key",EditCondition="Type == EDirectorNodeType::BindNPC && ActorSource == EDirectorActorSource::Object",EditConditionHides)) FName ObjectKey;
    UPROPERTY() FGuid Next;
    UPROPERTY() TArray<FGuid> NextNodes;
    UPROPERTY() TMap<FName,FGuid> ChoiceTargets;
    UPROPERTY() FGuid TrueTarget;
    UPROPERTY() FGuid FalseTarget;
    UPROPERTY() bool bForceCustomAnimation=true;
    UPROPERTY(EditAnywhere,Category="표시",meta=(DisplayName="플레이어 대역 (제어권 복귀 시 숨김)",EditCondition="Type == EDirectorNodeType::SpawnNPC || Type == EDirectorNodeType::BindNPC",EditConditionHides)) bool bPlayerStandIn=false;
    UPROPERTY(EditAnywhere,Category="표시",meta=(DisplayName="NPC 표시",EditCondition="Type == EDirectorNodeType::Visibility",EditConditionHides)) bool bVisible=true;
    UPROPERTY(EditAnywhere,Category="화면 페이드",meta=(DisplayName="시작 암전",ClampMin="0",ClampMax="1",EditCondition="Type == EDirectorNodeType::Fade",EditConditionHides)) float FadeFrom=0;
    UPROPERTY(EditAnywhere,Category="화면 페이드",meta=(DisplayName="종료 암전",ClampMin="0",ClampMax="1",EditCondition="Type == EDirectorNodeType::Fade",EditConditionHides)) float FadeTo=1;
    UPROPERTY(Instanced) TObjectPtr<AActor> ImportedTemplate;
    UPROPERTY(EditAnywhere,Category="이동 경로",meta=(DisplayName="경유점 리스트 사용",EditCondition="Type == EDirectorNodeType::CharacterMove || Type == EDirectorNodeType::CameraMove",EditConditionHides)) bool bUseMotionPath=false;
    UPROPERTY(EditAnywhere,Category="이동 경로",meta=(DisplayName="경유점 목록",TitleProperty="Time",EditCondition="bUseMotionPath && (Type == EDirectorNodeType::CharacterMove || Type == EDirectorNodeType::CameraMove)",EditConditionHides)) TArray<FDirectorMotionPoint> MotionPoints;
    UPROPERTY(EditAnywhere,Category="이동",meta=(DisplayName="이동 중 애니메이션 재생",EditCondition="Type == EDirectorNodeType::CharacterMove",EditConditionHides)) bool bPlayMoveAnimation=true;
    UPROPERTY(EditAnywhere,Category="애니메이션 블렌딩",meta=(DisplayName="재생 속도 직접 설정",EditCondition="Type == EDirectorNodeType::Animation",EditConditionHides)) bool bExplicitAnimationRate=false;
    UPROPERTY(EditAnywhere,Category="애니메이션 블렌딩",meta=(DisplayName="재생 속도",ClampMin="0.01",EditCondition="Type == EDirectorNodeType::Animation && bExplicitAnimationRate",EditConditionHides)) double AnimationRate=1;
    UPROPERTY(EditAnywhere,Category="애니메이션 블렌딩",meta=(DisplayName="시작 오프셋 (초)",ClampMin="0",EditCondition="Type == EDirectorNodeType::Animation",EditConditionHides)) float AnimationStartOffset=0;
    UPROPERTY(EditAnywhere,Category="애니메이션 블렌딩",meta=(DisplayName="끝 제외 구간 (초)",ClampMin="0",EditCondition="Type == EDirectorNodeType::Animation",EditConditionHides)) float AnimationEndOffset=0;
    UPROPERTY(EditAnywhere,Category="애니메이션 블렌딩",meta=(DisplayName="첫 루프 시작 오프셋 (초)",ClampMin="0",EditCondition="Type == EDirectorNodeType::Animation",EditConditionHides)) float AnimationFirstOffset=0;
    UPROPERTY(EditAnywhere,Category="애니메이션 블렌딩",meta=(DisplayName="역재생",EditCondition="Type == EDirectorNodeType::Animation",EditConditionHides)) bool bAnimationReverse=false;
    UPROPERTY(EditAnywhere,Category="애니메이션 블렌딩",meta=(DisplayName="블렌드 인 (초)",ClampMin="0",EditCondition="Type == EDirectorNodeType::Animation",EditConditionHides)) float AnimationBlendIn=0;
    UPROPERTY(EditAnywhere,Category="애니메이션 블렌딩",meta=(DisplayName="블렌드 아웃 (초)",ClampMin="0",EditCondition="Type == EDirectorNodeType::Animation",EditConditionHides)) float AnimationBlendOut=0;
    UPROPERTY(EditAnywhere,Category="애니메이션 블렌딩",meta=(DisplayName="가중치",ClampMin="0",ClampMax="1",EditCondition="Type == EDirectorNodeType::Animation",EditConditionHides)) float AnimationWeight=1;
    UPROPERTY(EditAnywhere,Category="애니메이션 블렌딩",meta=(DisplayName="블렌드 인 곡선",EditCondition="Type == EDirectorNodeType::Animation",EditConditionHides)) EMovieSceneBuiltInEasing AnimationEaseIn=EMovieSceneBuiltInEasing::CubicInOut;
    UPROPERTY(EditAnywhere,Category="애니메이션 블렌딩",meta=(DisplayName="블렌드 아웃 곡선",EditCondition="Type == EDirectorNodeType::Animation",EditConditionHides)) EMovieSceneBuiltInEasing AnimationEaseOut=EMovieSceneBuiltInEasing::CubicInOut;
    UPROPERTY(EditAnywhere,Category="애니메이션 블렌딩",meta=(DisplayName="다른 애니메이션과 중첩 허용",EditCondition="Type == EDirectorNodeType::Animation",EditConditionHides)) bool bAllowAnimationBlend=false;
    UPROPERTY(EditAnywhere,Category="시퀀스 재생",meta=(DisplayName="레벨 시퀀스",EditCondition="Type == EDirectorNodeType::Sequence",EditConditionHides)) TObjectPtr<ULevelSequence> SourceSequence;
    UPROPERTY(EditAnywhere,Category="시퀀스 재생",meta=(DisplayName="재생 속도",ClampMin="0.01",EditCondition="Type == EDirectorNodeType::Sequence",EditConditionHides)) float SequenceSpeed=1;
    UPROPERTY(EditAnywhere,EditFixedSize,Category="시퀀스 재생",meta=(DisplayName="역할 연결",TitleProperty="Label",EditCondition="Type == EDirectorNodeType::Sequence",EditConditionHides)) TArray<FDirectorSequenceRole> SequenceRoles;
    UPROPERTY() TArray<FDirectorSequenceComponent> SequenceComponents;
    UPROPERTY(EditAnywhere,Category="게임 액션",meta=(DisplayName="등록 액션 Key",GetOptions="GetActionKeys",EditCondition="Type == EDirectorNodeType::GameAction",EditConditionHides)) FName ActionKey;
    UPROPERTY(EditAnywhere,Category="게임 액션",meta=(DisplayName="대상 NPC Key (선택)",EditCondition="Type == EDirectorNodeType::GameAction",EditConditionHides)) FName ActionTarget;
    UPROPERTY(EditAnywhere,Category="게임 액션",meta=(DisplayName="액션 파라미터",EditCondition="Type == EDirectorNodeType::GameAction",EditConditionHides)) FDirectorActionParameters ActionParameters;
    UPROPERTY(EditAnywhere,Category="조건",meta=(DisplayName="조건 변수 Key",EditCondition="Type == EDirectorNodeType::Condition || Type == EDirectorNodeType::SetBool",EditConditionHides)) FName BoolKey;
    UPROPERTY(EditAnywhere,Category="조건",meta=(DisplayName="설정할 값",EditCondition="Type == EDirectorNodeType::SetBool",EditConditionHides)) bool BoolValue=true;
    UPROPERTY(EditAnywhere,Category="미리보기",meta=(DisplayName="미리보기 선택지 번호",ClampMin="1",ClampMax="4",EditCondition="Type == EDirectorNodeType::Dialogue",EditConditionHides)) int32 PreviewChoiceIndex=1;
    TArray<FGuid> AllSuccessors() const
    {
        if(Type==EDirectorNodeType::Condition)return {TrueTarget,FalseTarget};
        if(Type==EDirectorNodeType::Dialogue&&!Choices.IsEmpty()&&!ChoiceTargets.IsEmpty())
        {TArray<FGuid> Result;for(const auto& Choice:Choices)if(Choice.bEnabled)Result.Add(ChoiceTargets.FindRef(Choice.Key));return Result;}
        return Successors();
    }
    TArray<FGuid> Successors() const { return NextNodes.Num() ? NextNodes : (Next.IsValid() ? TArray<FGuid>{Next} : TArray<FGuid>{}); }
    UPROPERTY(EditAnywhere, Category="실행", meta=(DisplayName="완료 후 다음 실행", ToolTip="끄면 행동을 시작한 직후 다음 노드도 실행합니다. 합류 노드는 모든 경로의 행동 완료를 기다립니다.", EditCondition="Type == EDirectorNodeType::Sequence || Type == EDirectorNodeType::Camera || Type == EDirectorNodeType::Animation || Type == EDirectorNodeType::Wait || Type == EDirectorNodeType::CharacterMove || Type == EDirectorNodeType::CameraMove || Type == EDirectorNodeType::CameraPreset || Type == EDirectorNodeType::LookAt || Type == EDirectorNodeType::Expression || Type == EDirectorNodeType::CameraSwitch", EditConditionHides)) bool bWaitForCompletion = true;
    UPROPERTY(EditAnywhere, Category="연출", meta=(DisplayName="재생할 애니메이션", EditCondition="Type == EDirectorNodeType::Animation || (Type == EDirectorNodeType::CharacterMove && bPlayMoveAnimation && !bAutoLocomotion)", EditConditionHides)) TObjectPtr<UAnimSequence> Animation;
    UPROPERTY(VisibleAnywhere, Category="연출", meta=(DisplayName="동작")) EDirectorNodeType Type = EDirectorNodeType::Wait;
    UPROPERTY(EditAnywhere, Category="연출", meta=(DisplayName="NPC String Key", EditCondition="Type == EDirectorNodeType::Visibility || Type == EDirectorNodeType::SpawnNPC || Type == EDirectorNodeType::Camera || Type == EDirectorNodeType::Animation || Type == EDirectorNodeType::CharacterMove || Type == EDirectorNodeType::BindNPC || Type == EDirectorNodeType::CameraPreset || Type == EDirectorNodeType::LookAt || Type == EDirectorNodeType::Expression", EditConditionHides)) FName Role = TEXT("NPC");
    UPROPERTY(EditAnywhere, Category="연출", meta=(DisplayName="캐릭터 BP", EditCondition="Type == EDirectorNodeType::SpawnNPC || Type == EDirectorNodeType::BindNPC", EditConditionHides)) TSubclassOf<AActor> ActorClass;
    UPROPERTY(EditAnywhere, Category="연출", meta=(DisplayName="월드 위치와 회전", EditCondition="Type == EDirectorNodeType::SpawnNPC || Type == EDirectorNodeType::BindNPC", EditConditionHides)) FTransform Transform;
    UPROPERTY(EditAnywhere, Category="연출", meta=(DisplayName="시간 (초)", ClampMin="0.033334", EditCondition="Type == EDirectorNodeType::Fade || Type == EDirectorNodeType::Wait || Type == EDirectorNodeType::Camera || Type == EDirectorNodeType::Animation || (Type == EDirectorNodeType::CameraMove && !bUseMotionPath) || Type == EDirectorNodeType::CameraPreset || Type == EDirectorNodeType::LookAt || Type == EDirectorNodeType::Expression || Type == EDirectorNodeType::Dialogue || Type == EDirectorNodeType::CameraSwitch || (Type == EDirectorNodeType::GameplayReturn || Type == EDirectorNodeType::CameraReturn) || (Type == EDirectorNodeType::CharacterMove && !bUseMotionPath && MoveTiming == EDirectorMoveTiming::Duration)", EditConditionHides)) float Duration = 2.f;
    UPROPERTY() float FieldOfView = 50.f;
    UPROPERTY(EditAnywhere,Category="카메라 복귀",meta=(DisplayName="미리보기 복귀 구도 지정",EditCondition="(Type == EDirectorNodeType::GameplayReturn || Type == EDirectorNodeType::CameraReturn)",EditConditionHides)) bool bUsePreviewReturnView=false;
    UPROPERTY(EditAnywhere,Category="카메라 복귀",meta=(DisplayName="미리보기 복귀 위치·회전",ToolTip="실제 게임에서는 연출 시작 전 카메라로 복귀합니다. 이 값은 편집기 미리보기 전용입니다.",EditCondition="(Type == EDirectorNodeType::GameplayReturn || Type == EDirectorNodeType::CameraReturn) && bUsePreviewReturnView",EditConditionHides)) FTransform PreviewReturnView;
    UPROPERTY(EditAnywhere,Category="카메라 복귀",meta=(DisplayName="미리보기 복귀 화각",ClampMin="10",ClampMax="170",EditCondition="(Type == EDirectorNodeType::GameplayReturn || Type == EDirectorNodeType::CameraReturn) && bUsePreviewReturnView",EditConditionHides)) float PreviewReturnFOV=90;

    UPROPERTY(EditAnywhere, Category="연출", meta=(DisplayName="대상 바라보기", EditCondition="Type == EDirectorNodeType::Camera", EditConditionHides)) bool bLookAtTarget = true;
    UPROPERTY(EditAnywhere,Category="카메라",meta=(DisplayName="카메라 String Key",EditCondition="Type == EDirectorNodeType::Camera || Type == EDirectorNodeType::CameraMove || Type == EDirectorNodeType::CameraPreset || Type == EDirectorNodeType::CameraSwitch",EditConditionHides)) FName CameraKey;
    UPROPERTY(EditAnywhere,Category="이동",meta=(DisplayName="이동 위치 (cm)",EditCondition="!bUseMotionPath && (Type == EDirectorNodeType::CharacterMove || Type == EDirectorNodeType::CameraMove)",EditConditionHides)) FDirectorVectorInput Destination;
    UPROPERTY(EditAnywhere,Category="이동",meta=(DisplayName="회전 (X=Roll, Y=Pitch, Z=Yaw / 도)",EditCondition="Type == EDirectorNodeType::CameraMove && !bUseMotionPath",EditConditionHides)) FDirectorVectorInput Rotation;
    UPROPERTY(EditAnywhere,Category="이동",meta=(DisplayName="속도 / 시간 선택",EditCondition="Type == EDirectorNodeType::CharacterMove && !bUseMotionPath",EditConditionHides)) EDirectorMoveTiming MoveTiming=EDirectorMoveTiming::Speed;
    UPROPERTY(EditAnywhere,Category="이동",meta=(DisplayName="이동 속도 (cm/s)",ClampMin="0.01",EditCondition="Type == EDirectorNodeType::CharacterMove && !bUseMotionPath && MoveTiming == EDirectorMoveTiming::Speed",EditConditionHides)) float MoveSpeed=150;
    UPROPERTY(EditAnywhere,Category="이동",meta=(DisplayName="자체 걷기·달리기 자동 선택",EditCondition="Type == EDirectorNodeType::CharacterMove && bPlayMoveAnimation",EditConditionHides)) bool bAutoLocomotion=true;
    UPROPERTY(EditAnywhere,Category="이동",meta=(DisplayName="이 카메라로 촬영",EditCondition="Type == EDirectorNodeType::CameraMove || Type == EDirectorNodeType::CameraPreset",EditConditionHides)) bool bActivateCamera=true;
    UPROPERTY(EditAnywhere,Category="NPC 이동 기본값",meta=(DisplayName="걷기 애니메이션",EditCondition="Type == EDirectorNodeType::SpawnNPC || Type == EDirectorNodeType::BindNPC",EditConditionHides)) TObjectPtr<UAnimSequence> WalkAnimation;
    UPROPERTY(EditAnywhere,Category="NPC 이동 기본값",meta=(DisplayName="달리기 애니메이션",EditCondition="Type == EDirectorNodeType::SpawnNPC || Type == EDirectorNodeType::BindNPC",EditConditionHides)) TObjectPtr<UAnimSequence> RunAnimation;
    UPROPERTY(EditAnywhere,Category="NPC 이동 기본값",meta=(DisplayName="달리기 전환 속도 (cm/s)",ClampMin="0.01",EditCondition="Type == EDirectorNodeType::SpawnNPC || Type == EDirectorNodeType::BindNPC",EditConditionHides)) float RunThreshold=300;
    UPROPERTY(EditAnywhere,Category="캐릭터 기본값",meta=(DisplayName="연기 프로필",EditCondition="Type == EDirectorNodeType::SpawnNPC || Type == EDirectorNodeType::BindNPC",EditConditionHides)) TObjectPtr<USceneDirectorCharacterProfile> Profile;
    UPROPERTY(EditAnywhere,Category="기존 캐릭터",meta=(DisplayName="찾는 방식",EditCondition="Type == EDirectorNodeType::BindNPC",EditConditionHides)) EDirectorActorSource ActorSource=EDirectorActorSource::Player;
    UPROPERTY(EditAnywhere,Category="기존 캐릭터",meta=(DisplayName="Actor 태그",EditCondition="Type == EDirectorNodeType::BindNPC && ActorSource == EDirectorActorSource::Tag",EditConditionHides)) FName ActorTag;
    UPROPERTY(EditAnywhere,Category="연기",meta=(DisplayName="바라볼 NPC Key / 오버숄더 앞 인물",EditCondition="Type == EDirectorNodeType::LookAt || (Type == EDirectorNodeType::CameraPreset && Framing == EDirectorFraming::OverShoulder)",EditConditionHides)) FName TargetRole;
    UPROPERTY(EditAnywhere,Category="연기",meta=(DisplayName="표정 프리셋 Key",EditCondition="Type == EDirectorNodeType::Expression",EditConditionHides)) FName ExpressionKey;
    UPROPERTY(EditAnywhere,Category="연기",meta=(DisplayName="강도",ClampMin="0",ClampMax="1",EditCondition="Type == EDirectorNodeType::Expression || Type == EDirectorNodeType::LookAt",EditConditionHides)) float Strength=1;
    UPROPERTY(EditAnywhere,Category="연기",meta=(DisplayName="전환 시간 (초)",ClampMin="0",EditCondition="Type == EDirectorNodeType::Expression || Type == EDirectorNodeType::LookAt || Type == EDirectorNodeType::CameraSwitch",EditConditionHides)) float BlendSeconds=.25f;
    UPROPERTY(EditAnywhere,Category="구도",meta=(DisplayName="구도",EditCondition="Type == EDirectorNodeType::CameraPreset",EditConditionHides)) EDirectorFraming Framing=EDirectorFraming::Medium;
    UPROPERTY(EditAnywhere,Category="구도",meta=(DisplayName="좌우 각도 (도)",EditCondition="Type == EDirectorNodeType::CameraPreset",EditConditionHides)) float ShotYaw=20;
    UPROPERTY(EditAnywhere,Category="구도",meta=(DisplayName="위치 보정 (월드 cm)",EditCondition="Type == EDirectorNodeType::CameraPreset",EditConditionHides)) FVector ShotOffset=FVector::ZeroVector;
    UPROPERTY(EditAnywhere,Category="대사",meta=(DisplayName="화자 표시 방식",EditCondition="Type == EDirectorNodeType::Dialogue",EditConditionHides)) EDirectorSpeakerSource SpeakerSource=EDirectorSpeakerSource::Direct;
    UPROPERTY(EditAnywhere,Category="대사",meta=(DisplayName="등록 화자",RowType="/Script/SceneDirectorRuntime.DirectorSpeakerRow",EditCondition="Type == EDirectorNodeType::Dialogue && SpeakerSource == EDirectorSpeakerSource::Table",EditConditionHides)) FDataTableRowHandle SpeakerRow;
    UPROPERTY(EditAnywhere,Category="대사",meta=(DisplayName="화자 표시명",EditCondition="Type == EDirectorNodeType::Dialogue && SpeakerSource == EDirectorSpeakerSource::Direct",EditConditionHides)) FText SpeakerName;
    FText ResolveSpeaker() const;
    bool ValidateSpeaker(FString& Error) const;
    UPROPERTY(EditAnywhere,Category="대사",meta=(DisplayName="대사 (String Table 연결 가능)",MultiLine="true",EditCondition="Type == EDirectorNodeType::Dialogue",EditConditionHides)) FText DialogueText;
    UPROPERTY(EditAnywhere,Category="대사",meta=(DisplayName="선택지 (최대 4개)",TitleProperty="Text",EditCondition="Type == EDirectorNodeType::Dialogue",EditConditionHides)) TArray<FDirectorChoice> Choices;
    UPROPERTY(EditAnywhere,Category="대사",meta=(DisplayName="음성",EditCondition="Type == EDirectorNodeType::Dialogue",EditConditionHides)) TObjectPtr<USoundBase> Voice;
    UPROPERTY(EditAnywhere,Category="대사",meta=(DisplayName="진행 방식",EditCondition="Type == EDirectorNodeType::Dialogue",EditConditionHides)) EDirectorDialogueAdvance DialogueAdvance=EDirectorDialogueAdvance::Timed;
    UPROPERTY(EditAnywhere,Category="연출 모드",meta=(DisplayName="플레이어 숨김",EditCondition="Type == EDirectorNodeType::CinematicMode || Type == EDirectorNodeType::PlayerHidden",EditConditionHides)) bool bHidePlayer=false;
    UPROPERTY(EditAnywhere,Category="연출 모드",meta=(DisplayName="이동·시점 조작 잠금",EditCondition="Type == EDirectorNodeType::CinematicMode || Type == EDirectorNodeType::InputLock",EditConditionHides)) bool bLockInput=true;
    UPROPERTY(EditAnywhere,Category="연출 모드",meta=(DisplayName="게임 HUD 숨김",EditCondition="Type == EDirectorNodeType::CinematicMode || Type == EDirectorNodeType::HUDHidden",EditConditionHides)) bool bHideHUD=true;
    FName EffectiveCameraKey() const {return CameraKey.IsNone()?FName(*(TEXT("Camera_")+Id.ToString(EGuidFormats::Digits))):CameraKey;}
    UPROPERTY() FVector2D EditorPosition = FVector2D::ZeroVector;
};

USTRUCT()
struct FDirectorCue
{
    GENERATED_BODY()
    UPROPERTY() FDirectorStep Step;
    UPROPERTY() int32 StartFrame=0;
    UPROPERTY() int32 EndFrame=0;
};
UCLASS(BlueprintType)
class SCENEDIRECTORRUNTIME_API USceneDirectorAsset : public UDataAsset
{
    GENERATED_BODY()
public:
    // One authoring list; existing typed storage and save-game keys remain compatible.
    UPROPERTY(Transient,EditAnywhere,Category="공용 변수",meta=(DisplayName="변수 목록",TitleProperty="Key")) TArray<FDirectorVariableEntry> Variables;
    void RefreshVariableEntries();
    void ApplyVariableEntries();
    UFUNCTION(BlueprintCallable,Category="연출|편집") bool UpgradeControlNodes();
    UPROPERTY(EditAnywhere,Category="이벤트 실행 조건",meta=(DisplayName="모든 조건 충족 시 실행",TitleProperty="Key")) TArray<FDirectorEventCondition> EntryConditions;
    UPROPERTY(VisibleAnywhere,Category="이전 형식 (호환 저장)") TArray<FDirectorIntEntry> IntVariables;
    UPROPERTY(EditAnywhere,Category="연출 전체 배치 기준",meta=(DisplayName="연출 전체를 상호작용 Actor 기준으로 배치",ToolTip="등록 Vector3는 개별 노드 값입니다. 이 옵션은 NPC와 카메라 등 연출 전체를 제작 기준에서 상호작용 Actor 위치·방향으로 함께 변환합니다.")) bool bUseInteractionOrigin=false;
    USceneDirectorAsset* VariableOwner();
    USceneDirectorAsset* SelectEvent(const TMap<FName,bool>& Bools,const TMap<FName,int32>& Ints,FString& Error);
    void SyncVariables();
    UPROPERTY(EditAnywhere,Category="연출 전체 배치 기준",meta=(DisplayName="연출 제작 원점",EditCondition="bUseInteractionOrigin",EditConditionHides)) FTransform AuthoringOrigin;
    UPROPERTY(EditAnywhere,Category="오브젝트 목록",meta=(TitleProperty="Key",DisplayName="등록 오브젝트")) TArray<FDirectorObjectEntry> Objects;
    UPROPERTY(VisibleAnywhere,Category="변환 기록",meta=(DisplayName="보존된 원본")) TObjectPtr<ULevelSequence> ImportedFrom;
    UPROPERTY(VisibleAnywhere,Category="변환 기록",meta=(DisplayName="변환 보고서",MultiLine="true")) FString ImportReport;
    UPROPERTY(Transient) bool bResolvedBranchPath=false;
    UPROPERTY() FName EventKey=TEXT("Event_1");
    UPROPERTY(Instanced) TArray<TObjectPtr<USceneDirectorAsset>> EventGraphs;
    UFUNCTION(BlueprintPure,Category="연출",meta=(DisplayName="이벤트 그래프 찾기")) USceneDirectorAsset* FindEvent(FName Key) const;
    UPROPERTY() TArray<FDirectorStep> Steps;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="생성 결과") TObjectPtr<ULevelSequence> GeneratedSequence;
    UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="생성 결과",meta=(DisplayName="재생성 필요")) bool bNeedsCompile = true;
    UPROPERTY() int32 FormatVersion = 3;
    UPROPERTY() TArray<FDirectorCue> Cues;
    UPROPERTY() TMap<FName, FGuid> NPCBindings;
    UPROPERTY(EditAnywhere,Category="카메라 목록",meta=(TitleProperty="Key",DisplayName="저장 카메라")) TArray<FDirectorCameraEntry> Cameras;
    UPROPERTY(EditAnywhere,Category="Vector3 목록",meta=(TitleProperty="Key",DisplayName="저장 Vector3")) TArray<FDirectorVectorEntry> Vectors;
    UPROPERTY(VisibleAnywhere,Category="이전 형식 (호환 저장)") TArray<FDirectorBoolEntry> BoolVariables;
    UPROPERTY(EditAnywhere,Category="게임 액션",meta=(TitleProperty="Key",DisplayName="등록 액션 목록")) TArray<FDirectorActionEntry> Actions;
    UPROPERTY() TMap<FName,FGuid> CameraBindings;
    void EnsureCameraDefinitions();
    virtual void PostLoad() override;
#if WITH_EDITOR
    virtual void PreEditChange(FProperty* Property) override;
    virtual void PostEditChangeProperty(FPropertyChangedEvent& Event) override;
private:
    TArray<FDirectorVariableEntry> PreviousVariables;
    TArray<FDirectorCameraEntry> PreviousCameras;
    TArray<FDirectorVectorEntry> PreviousVectors;
    TArray<FDirectorBoolEntry> PreviousBools;
    TArray<FDirectorActionEntry> PreviousActions;
#endif
};
