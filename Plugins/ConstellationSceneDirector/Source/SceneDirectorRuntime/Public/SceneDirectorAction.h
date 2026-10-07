#pragma once
#include "CoreMinimal.h"
#include "UObject/Object.h"
#include "SceneDirectorAction.generated.h"
class ASceneDirectorPlayer;
class AActor;

USTRUCT(BlueprintType)
struct SCENEDIRECTORRUNTIME_API FDirectorActionParameters
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="액션",meta=(DisplayName="ID (퀘스트·아이템 등)")) FName Identifier;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="액션",meta=(DisplayName="수량")) int32 Amount=1;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="액션",meta=(DisplayName="수치")) float Value=0;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="액션",meta=(DisplayName="참/거짓")) bool Flag=true;
};

/** A synchronous game action. A fresh instance is created per node invocation. */
UCLASS(Abstract,Blueprintable,BlueprintType)
class SCENEDIRECTORRUNTIME_API USceneDirectorAction : public UObject
{
    GENERATED_BODY()
public:
    virtual UWorld* GetWorld() const override;
    // Override as a Blueprint function: return true on completion, false and Error on failure.
    UFUNCTION(BlueprintNativeEvent,Category="연출 액션",meta=(DisplayName="액션 실행"))
    bool Execute(ASceneDirectorPlayer* Player,AActor* Target,const FDirectorActionParameters& Parameters,FString& Error);
    virtual bool Execute_Implementation(ASceneDirectorPlayer* Player,AActor* Target,const FDirectorActionParameters& Parameters,FString& Error);
    // Useful BP example that does not touch saved quests or currency.
    UFUNCTION(BlueprintCallable,Category="연출 액션",meta=(DisplayName="대상 Actor 태그 설정"))
    static bool ApplyActorTag(AActor* Target,const FDirectorActionParameters& Parameters,FString& Error);
};

USTRUCT(BlueprintType)
struct SCENEDIRECTORRUNTIME_API FDirectorActionResult
{
    GENERATED_BODY()
    UPROPERTY(BlueprintReadOnly,Category="액션") FGuid NodeId;
    UPROPERTY(BlueprintReadOnly,Category="액션") FName ActionKey;
    UPROPERTY(BlueprintReadOnly,Category="액션") bool bSucceeded=false;
    UPROPERTY(BlueprintReadOnly,Category="액션") FString Message;
};
