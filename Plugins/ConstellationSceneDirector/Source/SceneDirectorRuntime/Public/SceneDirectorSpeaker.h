#pragma once
#include "CoreMinimal.h"
#include "Engine/DataTable.h"
#include "SceneDirectorSpeaker.generated.h"

UENUM(BlueprintType)
enum class EDirectorSpeakerSource : uint8
{
 Direct UMETA(DisplayName="직접 입력"),
 Table UMETA(DisplayName="화자 테이블에서 선택"),
 None UMETA(DisplayName="화자 없음")
};

// Row name is the stable speaker key; display name remains localizable FText.
USTRUCT(BlueprintType)
struct SCENEDIRECTORRUNTIME_API FDirectorSpeakerRow : public FTableRowBase
{
 GENERATED_BODY()
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="화자",meta=(DisplayName="화자 표시명")) FText DisplayName;
};
