#pragma once
#include "CoreMinimal.h"
class USceneDirectorAsset;
struct FDirectorStep;
namespace DirectorAuthoring
{
bool IsCharacterEntry(const FDirectorStep& Step);
TArray<FName> ReferenceKeys(const USceneDirectorAsset& Asset,FName Kind);
void RegisterDetails();
void UnregisterDetails();
}
