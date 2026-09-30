#pragma once

// The small state machine is independent of Unreal, so failure/reentry rules
// can be checked without running a game or altering a save slot.
class FSubwayTravelGate
{
public:
    bool Update(bool bInside, bool bLocalPlayer, bool bDestinationExists, bool bOtherTravelActive)
    {
        if (!bLocalPlayer) return false;
        if (!bInside) { bArmed = true; return false; }
        if (!bArmed) return false;
        bArmed = false;
        return bDestinationExists && !bOtherTravelActive;
    }
private:
    bool bArmed = true;
};
