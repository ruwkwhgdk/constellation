#pragma once
#include "CoreMinimal.h"

// Per actor, never stored on a shared notify object. Reopening a window preserves history.
struct FCombatHitLedger
{
    uint64 Begin() { End(); bActive = true; return ++Execution; }
    void End() { bActive = false; OpenWindows.Reset(); Hits.Reset(); }
    bool Open(FName Window)
    {
        if (!bActive || Window.IsNone()) return false;
        OpenWindows.Add(Window); return true;
    }
    void Close(FName Window) { OpenWindows.Remove(Window); }
    bool Claim(FName Window, UObject* Target)
    {
        if (!bActive || !OpenWindows.Contains(Window) || !IsValid(Target)) return false;
        auto& Targets = Hits.FindOrAdd(Window);
        if (Targets.Contains(Target)) return false;
        Targets.Add(Target); return true;
    }
    bool IsOpen(FName Window) const { return bActive && OpenWindows.Contains(Window); }
    const TSet<FName>& GetOpenWindows() const { return OpenWindows; }
    bool HasOpenWindow() const {return bActive && !OpenWindows.IsEmpty();}
    uint64 GetExecution() const { return Execution; }
private:
    uint64 Execution = 0;
    bool bActive = false;
    TSet<FName> OpenWindows;
    TMap<FName, TSet<TWeakObjectPtr<UObject>>> Hits;
};
