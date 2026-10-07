#pragma once
#include "CoreMinimal.h"
class USkeletalMeshComponent;

namespace CombatSurfaceContact
{
    // Select a point on the currently bone-skinned surface. Runs only on accepted hits.
    // Returns false (leaving outputs unchanged) when CPU geometry is unavailable.
    bool Resolve(USkeletalMeshComponent* Mesh, const FVector& Contact, const FVector& Normal,
        FVector& OutPosition, FVector& OutNormal, int32& OutTriangles);
    bool ConsiderTriangle(const FVector& Contact, const FVector& A, const FVector& B, const FVector& C,
        double& BestDistanceSquared, FVector& OutPosition);
}
