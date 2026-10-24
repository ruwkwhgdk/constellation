#pragma once
#include "CoreMinimal.h"
class UWorld;

namespace DirectorTesting
{
    SCENEDIRECTORRUNTIME_API bool IsSkipEnabled();
    SCENEDIRECTORRUNTIME_API void SetSkipEnabled(bool bEnabled);
    SCENEDIRECTORRUNTIME_API bool ShouldSkip(const UWorld* World);
}
