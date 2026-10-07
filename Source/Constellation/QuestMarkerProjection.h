#pragma once

#include "CoreMinimal.h"

namespace QuestMarkerProjection
{
// Behind-camera projection must retain the sign of clip X/Y, rather than mirror
// it by dividing by negative W. For edge clamping only the direction matters.
inline bool GetBehindCameraDirection(const FVector& WorldPosition, const FMatrix& ViewProjection,
	const FVector2D& ViewSize, FVector2D& OutDirection)
{
	OutDirection = FVector2D::ZeroVector;
	if (ViewSize.ContainsNaN() || ViewSize.X <= 0.0 || ViewSize.Y <= 0.0 || WorldPosition.ContainsNaN())
	{
		return false;
	}
	const FPlane Clip = ViewProjection.TransformFVector4(FVector4(WorldPosition, 1.0));
	if (!FMath::IsFinite(Clip.X) || !FMath::IsFinite(Clip.Y) || !FMath::IsFinite(Clip.W) || Clip.W > 0.0)
	{
		return false;
	}
	// Normalize before weighting so huge world coordinates cannot overflow the direction.
	const double Magnitude = FMath::Max(FMath::Abs(Clip.X), FMath::Abs(Clip.Y));
	if (Magnitude > 0.0)
	{
		OutDirection = FVector2D((Clip.X / Magnitude) * ViewSize.X, -(Clip.Y / Magnitude) * ViewSize.Y);
	}
	return !OutDirection.ContainsNaN();
}

inline FVector2D ClampDirectionToRectEdge(const FVector2D& Direction, const FVector2D& HalfExtents)
{
	if (FMath::IsNearlyZero(Direction.X) && FMath::IsNearlyZero(Direction.Y))
	{
		return FVector2D(0.f, -HalfExtents.Y);
	}

	// Compare the direction's slope against the rectangle's diagonal slope to decide whether the
	// ray exits through the left/right edge or the top/bottom edge, then scale to that edge.
	if (FMath::IsNearlyZero(Direction.X) || FMath::Abs(Direction.Y / Direction.X) > (HalfExtents.Y / HalfExtents.X))
	{
		const float Scale = HalfExtents.Y / FMath::Abs(Direction.Y);
		return FVector2D(Direction.X * Scale, Direction.Y > 0.f ? HalfExtents.Y : -HalfExtents.Y);
	}

	const float Scale = HalfExtents.X / FMath::Abs(Direction.X);
	return FVector2D(Direction.X > 0.f ? HalfExtents.X : -HalfExtents.X, Direction.Y * Scale);
}

}
