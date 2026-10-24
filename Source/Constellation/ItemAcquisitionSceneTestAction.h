#pragma once
#include "ItemAcquisitionSceneAction.h"
#include "ItemAcquisitionSceneTestAction.generated.h"

// Native test actions do not inherit mutable CDO object references like a BP
// generated action does. Resolve the fixture definition explicitly at execution.
UCLASS(NotBlueprintable,Transient)
class UItemAcquisitionSceneTestAction : public UItemAcquisitionSceneAction
{
 GENERATED_BODY()
public:
 virtual bool Execute_Implementation(ASceneDirectorPlayer* Player,AActor* Target,const FDirectorActionParameters& Parameters,FString& Error) override
 {
#if WITH_DEV_AUTOMATION_TESTS
  Definition=GetMutableDefault<UItemAcquisitionSceneAction>()->Definition;
  return Super::Execute_Implementation(Player,Target,Parameters,Error);
#else
  return false;
#endif
 }
};

UCLASS(NotBlueprintable,Transient)
class UItemAcquisitionNonblockingTestAction : public USceneDirectorAction
{
 GENERATED_BODY()
public:
 virtual bool Execute_Implementation(ASceneDirectorPlayer*,AActor*,const FDirectorActionParameters&,FString&) override {return true;}
};
