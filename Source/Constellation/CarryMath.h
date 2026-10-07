#pragma once
#include <cmath>

namespace CarryMath
{
    struct Vector { double X = 0, Y = 0, Z = 0; };
    inline bool CanLift(double ObjectKg, double CharacterKg, double Ratio)
    {
        return std::isfinite(ObjectKg) && std::isfinite(CharacterKg) && std::isfinite(Ratio)
            && ObjectKg > 0 && CharacterKg > 0 && Ratio > 0 && Ratio <= 1
            && ObjectKg <= CharacterKg * Ratio + 1.e-4; // Chaos mass roundoff: 0.1 gram tolerance.
    }
    inline bool SolveThrow(Vector Delta, double GravityZ, double Time, Vector& Velocity)
    {
        if (!std::isfinite(Delta.X) || !std::isfinite(Delta.Y) || !std::isfinite(Delta.Z)
            || !std::isfinite(GravityZ) || !std::isfinite(Time) || Time <= 0) return false;
        Velocity = {Delta.X / Time, Delta.Y / Time, (Delta.Z - .5 * GravityZ * Time * Time) / Time};
        return std::isfinite(Velocity.X) && std::isfinite(Velocity.Y) && std::isfinite(Velocity.Z);
    }
    inline double SpinDegreesPerSecond(double Distance, double MaximumDistance, double Time)
    {
        if (!std::isfinite(Distance) || !std::isfinite(MaximumDistance) || !std::isfinite(Time)
            || Distance <= 0 || MaximumDistance <= 0 || Time <= 0) return 0;
        const double Ratio = Distance < MaximumDistance ? Distance / MaximumDistance : 1;
        return 90 * Ratio / Time;
    }
}
