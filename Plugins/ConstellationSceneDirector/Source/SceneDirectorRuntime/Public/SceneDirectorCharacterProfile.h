#pragma once
#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "SceneDirectorCharacterProfile.generated.h"
USTRUCT(BlueprintType)
struct FDirectorExpressionPreset
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere,Category="표정",meta=(DisplayName="모프 가중치")) TMap<FName,float> Morphs;
};
UCLASS(BlueprintType)
class SCENEDIRECTORRUNTIME_API USceneDirectorCharacterProfile : public UDataAsset
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere,Category="캐릭터",meta=(DisplayName="메시 컴포넌트 이름 (비우면 첫 메시)")) FName MeshComponent;
    UPROPERTY(EditAnywhere,Category="시선",meta=(DisplayName="머리 본")) FName HeadBone=TEXT("head");
    UPROPERTY(EditAnywhere,Category="시선",meta=(DisplayName="머리 본의 정면 축")) FVector HeadForwardAxis=FVector(1,0,0);
    UPROPERTY(EditAnywhere,Category="구도",meta=(DisplayName="주시 높이 (캐릭터 원점 기준 cm)")) float AimHeight=150;
    UPROPERTY(EditAnywhere,Category="표정",meta=(DisplayName="표정 프리셋")) TMap<FName,FDirectorExpressionPreset> Expressions;
};
