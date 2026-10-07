#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SceneEventBinding.generated.h"
class USceneDirectorAsset;
class UBoxComponent;
UENUM(BlueprintType) enum class ESceneEventTrigger:uint8 { Volume UMETA(DisplayName="영역 진입"), Interaction UMETA(DisplayName="상호작용"), Combat UMETA(DisplayName="전투 종료"), LevelReady UMETA(DisplayName="레벨 준비 완료"), Destroyed UMETA(DisplayName="Actor 파괴"), LegacySequence UMETA(DisplayName="기존 시퀀스 요청 (이관)") };
UENUM(BlueprintType) enum class ESceneEventRepeat:uint8 { EveryTime UMETA(DisplayName="매번"), OncePerVisit UMETA(DisplayName="이번 레벨 방문에서 1회"), OncePerSave UMETA(DisplayName="저장 데이터 기준 1회") };
UENUM(BlueprintType) enum class ESceneEventOrigin:uint8 { Authored UMETA(DisplayName="제작 좌표"), Source UMETA(DisplayName="발동 대상"), Anchor UMETA(DisplayName="지정 앵커") };
UENUM(BlueprintType) enum class ESceneCombatResult:uint8 { Victory UMETA(DisplayName="승리"), Defeat UMETA(DisplayName="패배"), Any UMETA(DisplayName="결과 무관") };
UCLASS(BlueprintType,meta=(DisplayName="연출 이벤트 배치"))
class SCENEDIRECTORRUNTIME_API ASceneEventBinding:public AActor
{
 GENERATED_BODY()
public:
 ASceneEventBinding();
 UPROPERTY(EditAnywhere,Category="이벤트",meta=(DisplayName="사용")) bool bEnabled=true;
 UPROPERTY(EditAnywhere,Category="이벤트",meta=(DisplayName="발동 방식")) ESceneEventTrigger Trigger=ESceneEventTrigger::Volume;
 UPROPERTY(EditInstanceOnly,Category="이벤트",meta=(DisplayName="대상 Actor / 기존 Volume",EditCondition="Trigger != ESceneEventTrigger::LevelReady && Trigger != ESceneEventTrigger::Combat",EditConditionHides)) TObjectPtr<AActor> Source;
 UPROPERTY(EditAnywhere,Category="이벤트",meta=(DisplayName="실행할 연출")) TObjectPtr<USceneDirectorAsset> Director;
 UPROPERTY(EditAnywhere,Category="이관",meta=(DisplayName="기존 요청 시퀀스",EditCondition="Trigger == ESceneEventTrigger::LegacySequence",EditConditionHides)) TObjectPtr<class ULevelSequence> OriginalSequence;
 UPROPERTY(EditAnywhere,Category="실행 정책",meta=(DisplayName="반복 정책")) ESceneEventRepeat Repeat=ESceneEventRepeat::EveryTime;
 UPROPERTY(EditAnywhere,Category="실행 정책",meta=(DisplayName="변수 영속 저장")) bool bPersistVariables=false;
 UPROPERTY(EditAnywhere,Category="실행 정책",meta=(DisplayName="상태 공유 그룹 (빈 값이면 독립)")) FName StateGroup;
 UPROPERTY(EditAnywhere,Category="영역",meta=(DisplayName="시작부터 영역 안이면 실행",EditCondition="Trigger == ESceneEventTrigger::Volume",EditConditionHides)) bool bIncludeInitialOverlap=false;
 UPROPERTY(EditAnywhere,Category="전투",meta=(DisplayName="전투 Key",EditCondition="Trigger == ESceneEventTrigger::Combat",EditConditionHides)) FName CombatKey;
 UPROPERTY(EditAnywhere,Category="전투",meta=(DisplayName="결과",EditCondition="Trigger == ESceneEventTrigger::Combat",EditConditionHides)) ESceneCombatResult CombatResult=ESceneCombatResult::Victory;
 UPROPERTY(EditAnywhere,Category="레벨 시작",meta=(DisplayName="시작 순서",EditCondition="Trigger == ESceneEventTrigger::LevelReady",EditConditionHides)) int32 StartOrder=0;
 UPROPERTY(EditAnywhere,Category="연출 배치",meta=(DisplayName="배치 기준")) ESceneEventOrigin Origin=ESceneEventOrigin::Authored;
 UPROPERTY(EditInstanceOnly,Category="연출 배치",meta=(DisplayName="기준 앵커",EditCondition="Origin == ESceneEventOrigin::Anchor",EditConditionHides)) TObjectPtr<AActor> Anchor;
 UPROPERTY(EditInstanceOnly,Category="연출 배치",meta=(DisplayName="오브젝트 Key → Actor")) TMap<FName,TObjectPtr<AActor>> Objects;
 UPROPERTY(EditAnywhere,Category="영역",meta=(DisplayName="자체 영역 반크기 (cm)",ClampMin="1",EditCondition="Trigger == ESceneEventTrigger::Volume",EditConditionHides)) FVector AreaExtent=FVector(150,150,100);
 UPROPERTY(VisibleAnywhere,Category="영역") TObjectPtr<UBoxComponent> Area;
 UPROPERTY(VisibleInstanceOnly,Category="식별") FGuid EventId;
 UPROPERTY(VisibleInstanceOnly,Transient,Category="실행 상태") FString Status=TEXT("준비");
 bool Validate(FString& Error,bool bAfterDestruction=false) const;
 FString StateKey() const;
 bool PlayerInside() const;
 FTransform CaptureOrigin() const;
 UFUNCTION(BlueprintCallable,Category="연출 이벤트",meta=(DisplayName="발동 시험 (게임 액션 실행)")) void TestSignal();
 virtual void OnConstruction(const FTransform& Transform) override;
#if WITH_EDITOR
 virtual void PostDuplicate(EDuplicateMode::Type DuplicateMode) override;
 virtual void PostEditImport() override;
#endif
protected:
 virtual void BeginPlay() override;
 virtual void EndPlay(const EEndPlayReason::Type Reason) override;
 UFUNCTION() void Enter(AActor* Overlapped,AActor* Other);
 UFUNCTION() void Leave(AActor* Overlapped,AActor* Other);
 UFUNCTION() void SourceDestroyed(AActor* Actor);
private:
 friend class FSceneEventInitialOverlapTest;
 TWeakObjectPtr<AActor> Watched;
 bool bInside=false;
 bool bVolumeArmed=false;
};
