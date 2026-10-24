#pragma once
#include "CoreMinimal.h"
#include "Engine/Texture2D.h"
#include "Styling/SlateBrush.h"
namespace ChoiceStardust
{
inline FSlateBrush Brush(UTexture2D* Atlas,int32 Part)
{
 const FVector2f Min[]={{150,130},{150,394},{410,675},{917,686}};
 const FVector2f Max[]={{1386,342},{1386,600},{638,915},{1130,914}};
 FSlateBrush B;B.SetResourceObject(Atlas);B.DrawAs=ESlateBrushDrawType::Image;
 B.ImageSize=Part<2?FVector2f(424,72):FVector2f(38,40);
 B.SetUVRegion(FBox2f(Min[Part]/FVector2f(1536,1024),Max[Part]/FVector2f(1536,1024)));
 return B;
}
inline FSlateBrush LockedBrush(UTexture2D* Atlas,int32 Part)
{
 const FVector2f Min[]={{46,160},{268,466},{912,466}};
 const FVector2f Max[]={{1490,425},{630,948},{1274,948}};
 FSlateBrush B;B.SetResourceObject(Atlas);B.DrawAs=ESlateBrushDrawType::Image;
 B.ImageSize=Part==0?FVector2f(424,72):FVector2f(34,42);
 B.TintColor=Part==0?FLinearColor(.4f,.4f,.4f,1.f):FLinearColor(.7f,.7f,.7f,1.f);
 B.SetUVRegion(FBox2f(Min[Part]/FVector2f(1536,1024),Max[Part]/FVector2f(1536,1024)));
 return B;
}
inline float Sparkle(float Time){return .7f+.3f*FMath::Sin(Time*3.f);}
}
