#pragma once
#include "CoreMinimal.h"
#include "Engine/Texture2D.h"
#include "Styling/SlateBrush.h"
namespace TutorialToastStyle
{
inline FSlateBrush Brush(UTexture2D* Atlas,int32 Part)
{
 const FVector2f Min[]={{88,112},{695,554}};
 const FVector2f Max[]={{1448,502},{840,956}};
 FSlateBrush B;B.SetResourceObject(Atlas);B.DrawAs=ESlateBrushDrawType::Image;
 B.ImageSize=Part==0?FVector2f(420,132):FVector2f(22,94);
 B.SetUVRegion(FBox2f(Min[Part]/FVector2f(1536,1024),Max[Part]/FVector2f(1536,1024)));
 return B;
}
}
