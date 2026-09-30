#include "../Source/Constellation/SubwayTravelGate.h"
#include <cstdio>

int main()
{
    int Failures = 0;
    auto Check = [&](bool Value, const char* Message) { if (!Value) { std::printf("FAIL: %s\n", Message); ++Failures; } };
    FSubwayTravelGate Gate;
    Check(!Gate.Update(false, true, true, false), "outside cannot travel");
    Check(!Gate.Update(true, false, true, false), "nonplayer cannot travel");
    Check(Gate.Update(true, true, true, false), "local player entering valid zone travels");
    Check(!Gate.Update(true, true, true, false), "no duplicate travel while still inside");
    Check(!Gate.Update(false, true, true, false), "leaving rearms without travelling");
    Check(Gate.Update(true, true, true, false), "reentry after failure can retry");
    FSubwayTravelGate Missing;
    Check(!Missing.Update(true, true, false, false), "missing map keeps pawn in safe source area");
    Check(!Missing.Update(true, true, true, false), "failed attempt requires leaving before retry");
    Missing.Update(false, true, true, false);
    Check(Missing.Update(true, true, true, false), "fixed map may retry on reentry");
    FSubwayTravelGate Arrival;
    Check(!Arrival.Update(true, true, true, true), "arrival suppression prevents bounceback");
    Check(!Arrival.Update(true, true, true, false), "arrival suppression ending inside does not bounce");
    Arrival.Update(false, true, true, false);
    Check(Arrival.Update(true, true, true, false), "later deliberate reentry permits return");
    std::printf("%d failures\n", Failures);
    return Failures ? 1 : 0;
}
