#pragma once
#include "CoreMinimal.h"

// A presentation-only prefix. The localized source is returned intact on completion.
class SCENEDIRECTORRUNTIME_API FDirectorDialogueReveal
{
public:
    void Reset(const FText& Text,float SecondsPerCharacter,float MaxDuration=0.f);
    bool Advance(float DeltaSeconds);
    bool Finish();
    bool IsRevealing() const {return Visible<Ends.Num();}
    FText GetText() const;
private:
    FText Source;
    FString Markup;
    TArray<int32> Ends,Depths;
    int32 Visible=0;
    double Elapsed=0,Interval=0;
};
