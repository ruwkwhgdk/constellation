#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "SceneDirectorInteractionComponent.generated.h"
class USceneDirectorAsset;
class ASceneDirectorPlayer;
UCLASS(ClassGroup=(SceneDirector),meta=(BlueprintSpawnableComponent,DisplayName="Ac_SceneDirectorInteraction"))
class SCENEDIRECTORRUNTIME_API USceneDirectorInteractionComponent:public UActorComponent
{
 GENERATED_BODY()
public:
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="연출",meta=(DisplayName="실행할 연출")) TObjectPtr<USceneDirectorAsset> Director;
 UPROPERTY(Transient,BlueprintReadOnly,Category="연출") FString LastError;
 UPROPERTY(Transient,BlueprintReadOnly,Category="연출") TObjectPtr<ASceneDirectorPlayer> ActivePlayer;
 UFUNCTION(BlueprintCallable,Category="연출") static bool RouteInteraction(AActor* Owner,AActor* Interactor);
 UFUNCTION(BlueprintCallable,Category="연출") void Cancel();
 bool HandleInteraction(AActor* Interactor);
protected:
 virtual void EndPlay(const EEndPlayReason::Type Reason) override;
 UFUNCTION() void Finished(bool Completed);
};
