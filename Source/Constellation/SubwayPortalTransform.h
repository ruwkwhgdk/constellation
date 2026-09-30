#pragma once
#include "CoreMinimal.h"
struct FSubwayPortalPose
{
    FVector Location;
    FQuat Rotation;
    FVector Velocity;
};
// Both frames are authored at floor height with unit scale.
inline FSubwayPortalPose SubwayPortalTransform(const FTransform &Source,
                                               const FTransform &Destination,
                                               const FVector &Location, const FQuat &Rotation,
                                               const FVector &Velocity)
{
    const FQuat Delta = Destination.GetRotation() * Source.GetRotation().Inverse();
    return {Destination.TransformPosition(Source.InverseTransformPosition(Location)),
            Delta * Rotation, Delta.RotateVector(Velocity)};
}
