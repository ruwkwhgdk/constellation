#pragma once
#include "CoreMinimal.h"
#include "Factories/Factory.h"
#include "SceneDirectorFactory.generated.h"
UCLASS()
class USceneDirectorFactory : public UFactory
{
    GENERATED_BODY()
public:
    USceneDirectorFactory();
    virtual UObject* FactoryCreateNew(UClass* Class,UObject* Parent,FName Name,EObjectFlags Flags,UObject* Context,FFeedbackContext* Warn) override;
};
