#pragma once
#include "CoreMinimal.h"
class USceneDirectorAsset;

// Read-only navigation. Uses persisted Step.Id, never the regenerated editor NodeGuid.
SCENEDIRECTOREDITOR_API bool OpenDirectorTextLocation(USceneDirectorAsset* Root,const FSoftObjectPath& EventPath,FGuid StepId,FName ChoiceKey,FName FieldName,FText& OutMessage);
