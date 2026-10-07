#include "../Source/Constellation/CarryMath.h"
#include <cstdio>
#include <limits>
#include <initializer_list>

int main()
{
    int Failures = 0;
    auto Check = [&](bool Result, const char* Name)
    {
        if (!Result) { std::printf("FAIL: %s\n", Name); ++Failures; }
    };
    Check(CarryMath::CanLift(9.99, 50, .2), "Below weight limit accepted");
    Check(CarryMath::CanLift(10, 50, .2), "Exact weight limit accepted");
    Check(CarryMath::CanLift(10.000001, 50, .2), "Physics mass roundoff accepted");
    Check(!CarryMath::CanLift(10.01, 50, .2), "Above weight limit rejected");
    Check(!CarryMath::CanLift(-1, 50, .2), "Negative object mass rejected");
    Check(!CarryMath::CanLift(0, 50, .2), "Zero object mass rejected");
    Check(!CarryMath::CanLift(1, 0, .2), "Zero character mass rejected");
    Check(!CarryMath::CanLift(1, 50, -.2), "Negative ratio rejected");
    Check(!CarryMath::CanLift(std::numeric_limits<double>::quiet_NaN(), 50, .2), "NaN mass rejected");
    Check(!CarryMath::CanLift(1, std::numeric_limits<double>::infinity(), .2), "Infinite mass rejected");
    for (double TargetZ : {-200.0, 0.0, 200.0})
    {
        CarryMath::Vector Velocity;
        Check(CarryMath::SolveThrow({300, 400, TargetZ}, -980, 1, Velocity), "Throw solved");
        // At 1 second, XY must be (300,400); gravity contributes -490 cm in Z.
        Check(std::abs(Velocity.X - 300) < 1e-8 && std::abs(Velocity.Y - 400) < 1e-8,
              "Horizontal velocity reaches hand-checked target");
        Check(std::abs(Velocity.Z - 490 - TargetZ) < 1e-8, "Vertical velocity compensates gravity");
    }
    CarryMath::Vector Velocity;
    Check(!CarryMath::SolveThrow({1, 0, 0}, -980, 0, Velocity), "Zero time rejected");
    Check(!CarryMath::SolveThrow({1, 0, 0}, -980, -1, Velocity), "Negative time rejected");
    Check(!CarryMath::SolveThrow({0, 0, std::numeric_limits<double>::infinity()}, -980, 1, Velocity), "Nonfinite target rejected");
    Check(std::abs(CarryMath::SpinDegreesPerSecond(500, 1000, 1) - 45) < 1e-8, "Half distance spin is 45 degrees per second");
    Check(std::abs(CarryMath::SpinDegreesPerSecond(2000, 1000, 2) - 45) < 1e-8, "Spin capped at 90 degrees per flight");
    Check(CarryMath::SpinDegreesPerSecond(1, 0, 1) == 0, "Invalid maximum distance safe");
    Check(CarryMath::SpinDegreesPerSecond(1, 1, 0) == 0, "Invalid flight time safe");
    std::printf("Carry math: %d failures\n", Failures);
    return Failures ? 1 : 0;
}
