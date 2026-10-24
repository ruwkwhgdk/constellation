#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "SceneDirectorAction.h"
#include "ItemAcquisitionTypes.h"
#include "ItemAcquisitionSceneAction.generated.h"
class UItemAcquisitionDefinition;

/** Runtime owner for a synchronous director action's asynchronous presentation. */
UCLASS(Transient)
class CONSTELLATION_API UItemAcquisitionSceneLease : public UActorComponent
{
 GENERATED_BODY()
public:
 bool Begin(const FItemAcquisitionPresentation& Presentation,FKey Key,FString& Error);
protected:
 virtual void EndPlay(const EEndPlayReason::Type Reason) override;
private:
 friend class FItemAcquisitionSceneBridgeTest;
 FGuid RequestId;
 bool bPending=false,bPreviousPaused=false;
 void Resolve(bool Confirmed);
 void CancelPending();
 UFUNCTION() void DirectorStopped(bool Completed);
};

/** Register a BP subclass in SceneDirector Actions and select it on a GameAction node.
 * Definition is presentation only; node Amount supplies its displayed quantity.
 * The authored event retains all grant policy. */
UCLASS(Blueprintable)
class CONSTELLATION_API UItemAcquisitionSceneAction : public USceneDirectorAction
{
 GENERATED_BODY()
public:
 UPROPERTY(EditDefaultsOnly,BlueprintReadOnly,Category="Item Acquisition") TObjectPtr<UItemAcquisitionDefinition> Definition;
 // Empty resolves the current IA_Interact binding through the presentation subsystem.
 UPROPERTY(EditDefaultsOnly,BlueprintReadOnly,Category="Item Acquisition") FKey ConfirmKey;
 virtual bool RequiresPresentationBoundary() const override {return true;}
 virtual bool Execute_Implementation(ASceneDirectorPlayer* Player,AActor* Target,const FDirectorActionParameters& Parameters,FString& Error) override;
};
