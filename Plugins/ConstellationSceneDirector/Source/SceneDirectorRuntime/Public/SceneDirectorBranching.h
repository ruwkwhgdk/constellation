#pragma once
#include "CoreMinimal.h"
class USceneDirectorAsset;
namespace DirectorBranching
{
SCENEDIRECTORRUNTIME_API bool HasBranches(const USceneDirectorAsset& Source);
SCENEDIRECTORRUNTIME_API bool Resolve(const USceneDirectorAsset& Source,const TMap<FGuid,FName>& Decisions,const TMap<FName,bool>& InitialOverrides,USceneDirectorAsset& Out,FGuid& PendingChoice,FString& Error);
SCENEDIRECTORRUNTIME_API bool ValidateAll(const USceneDirectorAsset& Source,FString& Error);
}
