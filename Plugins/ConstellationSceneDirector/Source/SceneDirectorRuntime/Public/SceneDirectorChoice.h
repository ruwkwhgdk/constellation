#pragma once
#include "CoreMinimal.h"
#include "Engine/DataTable.h"
#include "SceneDirectorChoice.generated.h"
class UTexture2D;
USTRUCT(BlueprintType)
struct SCENEDIRECTORRUNTIME_API FDirectorChoice
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="선택지",meta=(DisplayName="결과 Key",IgnoreForMemberInitializationTest)) FName Key=FName(*FGuid::NewGuid().ToString(EGuidFormats::Digits));
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="선택지",meta=(DisplayName="선택 가능")) bool bEnabled=true;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="선택지",meta=(DisplayName="선택 불가 사유",EditCondition="!bEnabled")) FText DisabledReason;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="선택지",meta=(DisplayName="선택지 문구",MultiLine="true")) FText Text=FText::FromString(TEXT("선택지"));
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="선택지",meta=(DisplayName="선택지 문구 데이터 행 (선택)")) FDataTableRowHandle TextRow;
    UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="선택지",meta=(DisplayName="선택 불가 사유 데이터 행 (선택)",EditCondition="!bEnabled")) FDataTableRowHandle DisabledReasonRow;
    FText ResolveText() const;
    FText ResolveDisabledReason() const;
};
USTRUCT()
struct SCENEDIRECTORRUNTIME_API FDirectorChoiceStyle
{
    GENERATED_BODY()
    UPROPERTY() TObjectPtr<UTexture2D> FocusedBG;
    UPROPERTY() TObjectPtr<UTexture2D> FocusedStroke;
    UPROPERTY() TObjectPtr<UTexture2D> IdleBG;
    UPROPERTY() TObjectPtr<UTexture2D> IdleStroke;
    UPROPERTY() TObjectPtr<UTexture2D> Cursor;
    UPROPERTY() TObjectPtr<UTexture2D> LockedAtlas;
};
namespace DirectorChoices
{
    SCENEDIRECTORRUNTIME_API bool Validate(const TArray<FDirectorChoice>& Choices,FString& Error);
}
