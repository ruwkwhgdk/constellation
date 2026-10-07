#pragma once
#include "CoreMinimal.h"
#include "Bindings/MovieSceneCustomBinding.h"
#include "SceneDirectorSequence.generated.h"
class USceneDirectorAsset;
class ULevelSequence;
class UActorComponent;
struct FDirectorStep;
UENUM()
enum class EDirectorSequenceTarget : uint8 { Original UMETA(DisplayName="원본 Spawnable 사용"), NPC UMETA(DisplayName="NPC Key"), Camera UMETA(DisplayName="카메라 Key") };
USTRUCT()
struct SCENEDIRECTORRUNTIME_API FDirectorSequenceRole
{
    GENERATED_BODY()
    UPROPERTY() FGuid Binding;
    UPROPERTY(VisibleAnywhere,Category="역할",meta=(DisplayName="원본 역할")) FString Label;
    UPROPERTY() TSubclassOf<UObject> SourceClass;
    UPROPERTY(EditAnywhere,Category="역할",meta=(DisplayName="연결 방식")) EDirectorSequenceTarget Target=EDirectorSequenceTarget::NPC;
    UPROPERTY(EditAnywhere,Category="역할",meta=(DisplayName="대상 String Key",EditCondition="Target != EDirectorSequenceTarget::Original",EditConditionHides)) FName Key;
};
USTRUCT()
struct FDirectorSequenceComponent
{
    GENERATED_BODY()
    UPROPERTY() FGuid Binding;
    UPROPERTY() FGuid Parent;
    UPROPERTY() FName Name;
    UPROPERTY() TSubclassOf<UActorComponent> ComponentClass;
};
/** Resolves the same root actor in Sequencer previews and LevelSequence runtime players. */
UCLASS()
class SCENEDIRECTORRUNTIME_API UDirectorSequenceBinding : public UMovieSceneCustomBinding
{
    GENERATED_BODY()
public:
    UPROPERTY() FGuid RootBinding;
    UPROPERTY() TSubclassOf<UObject> ObjectClass;
    UPROPERTY() FName ComponentName;
    UPROPERTY() bool bComponent=false;
    virtual FMovieSceneBindingResolveResult ResolveBinding(const FMovieSceneBindingResolveParams&,int32,TSharedRef<const UE::MovieScene::FSharedPlaybackState> State) const override;
    virtual bool SupportsBindingCreationFromObject(const UObject*) const override{return false;}
    virtual UMovieSceneCustomBinding* CreateNewCustomBinding(UObject*,UMovieScene&) override{return nullptr;}
    virtual UClass* GetBoundObjectClass() const override{return ObjectClass?ObjectClass.Get():UObject::StaticClass();}
#if WITH_EDITOR
    virtual FText GetBindingTypePrettyName() const override{return FText::FromString(TEXT("Scene Director 역할"));}
#endif
};
namespace DirectorSequence
{
    SCENEDIRECTORRUNTIME_API void RefreshRoles(FDirectorStep& Step);
    SCENEDIRECTORRUNTIME_API bool Validate(const FDirectorStep& Step,const USceneDirectorAsset& Asset,double& Seconds,FString& Error);
    SCENEDIRECTORRUNTIME_API bool HasCamera(const FDirectorStep& Step);
    SCENEDIRECTORRUNTIME_API bool UsesNPC(const FDirectorStep& Step,FName Key);
    SCENEDIRECTORRUNTIME_API bool UsesCamera(const FDirectorStep& Step,FName Key);
    SCENEDIRECTORRUNTIME_API bool Add(ULevelSequence& Root,const FDirectorStep& Step,int32 Begin,int32 End,const TMap<FName,FGuid>& NPCs,const TMap<FName,FGuid>& Cameras,FString& Error);
}
