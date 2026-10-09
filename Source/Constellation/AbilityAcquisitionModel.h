#pragma once
#include "CoreMinimal.h"
namespace AbilityAcquisition
{
inline bool ShouldPresent(int32 Slot,int32 Mask,bool Unlock){return Slot>=0&&Slot<3&&Unlock&&(Mask&(1<<Slot))==0;}
inline float Fade(double T,double A,double B){const float X=FMath::Clamp(float((T-A)/(B-A)),0.f,1.f);return X*X*(3.f-2.f*X);}
inline bool CanDismiss(double Elapsed,bool Repeat,bool Exiting){return Elapsed>=6.2&&!Repeat&&!Exiting;}
inline FVector2D Position(int32 I){static const FVector2D P[]={{1202,636.75},{1361,424.85},{1006,677.05},{837,697.85},{644,622.45},{1232,231.15},{560,362.45}};return P[FMath::Clamp(I,0,6)];}
inline int32 Link(int32 I){static const int32 Order[]={6,4,3,2,0,1,5};return Order[FMath::Clamp(I,0,6)];}
}
