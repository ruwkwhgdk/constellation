#pragma once
#include "CoreMinimal.h"
class ULevelSequence;
class USceneDirectorAsset;
class SCENEDIRECTOREDITOR_API FSceneDirectorImporter
{
public:
    static USceneDirectorAsset* Convert(ULevelSequence* Source,UObject* Outer,FString& Report);
};
