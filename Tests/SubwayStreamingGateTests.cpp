#include "../Source/Constellation/SubwayStreamingGate.h"
#include <cstdio>
int main()
{
    int failures = 0;
    auto check = [&](bool v, const char *msg) {
        if (!v)
        {
            ++failures;
            std::printf("FAIL %s\n", msg);
        }
    };
    FSubwayStreamingGate g;
    check(!g.Update(-100, true, true, false), "approach does not cross");
    check(!g.Update(10, true, false, false), "loading holds player safely");
    check(g.Update(10, true, true, false), "ready while waiting can cross without reentry");
    check(g.Update(10, true, true, false), "failed destination collision check can retry");
    g.Commit();
    check(!g.Update(10, true, true, false), "committed crossing cannot repeat");
    check(!g.Update(-50, true, true, false), "return approach rearms");
    check(!g.Update(10, false, true, false), "outside tunnel cannot cross");
    check(!g.Update(10, true, true, true), "handoff cooldown prevents bounce");
    check(g.Update(10, true, true, false), "deliberate return works");
    check(SubwayCanRetryLoad(true, true, 70, 0), "fully unloaded timed out attempt may retry once");
    check(!SubwayCanRetryLoad(true, false, 80, 0), "never duplicate an instance still unloading");
    check(!SubwayCanRetryLoad(true, true, 69, 0), "retry observes cooldown");
    check(!SubwayCanRetryLoad(true, true, 80, 1), "retry budget prevents infinite reloads");
    check(!SubwayCanRetryLoad(false, true, 80, 0), "healthy request is not retried");
    std::printf("%d streaming gate failures\n", failures);
    return failures ? 1 : 0;
}
