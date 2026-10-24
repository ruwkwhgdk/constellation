#include "SceneDirectorTesting.h"
#include "Engine/World.h"
#include "HAL/IConsoleManager.h"
#include "Engine/Engine.h"
#include "EngineUtils.h"
#include "SceneDirectorPlayer.h"

#if WITH_EDITOR
static TAutoConsoleVariable<int32> CVarSkipCinematics(
    TEXT("SceneDirector.SkipCinematics"), 0,
    TEXT("Skip Scene Director requests in PIE/SIE without executing actions or recording completion."));
#endif

bool DirectorTesting::IsSkipEnabled()
{
#if WITH_EDITOR
    return CVarSkipCinematics.GetValueOnGameThread() != 0;
#else
    return false;
#endif
}

void DirectorTesting::SetSkipEnabled(bool bEnabled)
{
#if WITH_EDITOR
    CVarSkipCinematics->Set(bEnabled ? 1 : 0, ECVF_SetByCode);
    if(bEnabled && GEngine)
    {
        // Snapshot before stopping: callbacks can destroy players and bindings.
        TArray<TWeakObjectPtr<ASceneDirectorPlayer>> Players;
        for(const auto& Context:GEngine->GetWorldContexts())
            if(UWorld* World=Context.World();ShouldSkip(World))
                for(TActorIterator<ASceneDirectorPlayer> It(World);It;++It)
                    if(It->IsDirectorPlaying())Players.Add(*It);
        for(auto Weak:Players)if(auto* Player=Weak.Get())Player->StopDirector();
    }
#endif
}

bool DirectorTesting::ShouldSkip(const UWorld* World)
{
    return World && World->WorldType == EWorldType::PIE && IsSkipEnabled();
}
