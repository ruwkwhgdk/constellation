#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "AITypes.h"
#include "CombatEnemyAgent.generated.h"
class UCombatEncounterProfile;
class ACombatLabCharacter;
class AAIController;
class APawn;
struct FPathFollowingResult;
UENUM(BlueprintType)
enum class ECombatEnemyState : uint8 { Idle,Chasing,Searching,Fighting,Returning,Blocked,Dead };
UCLASS(ClassGroup=Combat,meta=(BlueprintSpawnableComponent))
class COMBATRUNTIME_API UCombatEnemyAgent : public UActorComponent
{
    GENERATED_BODY()
public:
    UCombatEnemyAgent();
    void Initialize(UCombatEncounterProfile* InProfile);
    virtual void TickComponent(float Delta,ELevelTick TickType,FActorComponentTickFunction* ThisTickFunction) override;
    UFUNCTION(BlueprintPure,Category="Combat|AI") bool CanAttack() const { return State==ECombatEnemyState::Fighting && Target.IsValid(); }
    bool IsManaging() const { return bInitialized; }
    uint64 GetEncounterEpoch() const { return EncounterEpoch; }
    FVector GetHome() const { return Home; }
    APawn* GetTarget() const { return Target.Get(); }
    UPROPERTY(BlueprintReadOnly,Category="Combat|AI") ECombatEnemyState State=ECombatEnemyState::Idle;
    UPROPERTY(BlueprintReadOnly,Category="Combat|AI") FString Decision;
protected:
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
private:
    UPROPERTY() TObjectPtr<UCombatEncounterProfile> Profile;
    TWeakObjectPtr<ACombatLabCharacter> Fighter;
    TWeakObjectPtr<AAIController> Controller;
    TWeakObjectPtr<APawn> Target;
    FVector Home,LastSeen,LastGoal,ProgressLocation;
    float Time=0,LastSightTime=0,NextMoveTime=0,LastProgressTime=0,AcquireAfter=0;
    int32 MoveFailures=0;
    FAIRequestID MoveId;
    FDelegateHandle MoveEndHandle;
    uint64 EncounterEpoch=0;
    bool bInitialized=false,bStopping=false;
    bool HasSight(APawn* Other) const;
    void StopMove();
    void ReturnHome(const FString& Reason);
    void Move(const FVector& Goal,float Radius);
    void MoveFailed();
    void MoveEnded(FAIRequestID Request,const FPathFollowingResult& Result);
};
