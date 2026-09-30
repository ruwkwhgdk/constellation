#include "SubwayTunnelEnvironment.h"
#include "Components/BoxComponent.h"
#include "Components/PostProcessComponent.h"
ASubwayTunnelEnvironment::ASubwayTunnelEnvironment()
{
    Bounds = CreateDefaultSubobject<UBoxComponent>(TEXT("TunnelBounds"));
    SetRootComponent(Bounds);
    Bounds->SetBoxExtent(FVector(500, 210, 150));
    Bounds->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Bounds->SetHiddenInGame(true);
    PostProcess = CreateDefaultSubobject<UPostProcessComponent>(TEXT("TunnelExposure"));
    PostProcess->SetupAttachment(Bounds);
    PostProcess->bUnbound = false;
    PostProcess->BlendRadius = 180;
    PostProcess->Priority = 100;
    PostProcess->BlendWeight = 1;
    auto &S = PostProcess->Settings;
    // Preserve the surrounding camera's meter and physical-exposure convention.
    // Switching those enum/bool settings at a blend boundary causes a bright flash.
    S.bOverride_AutoExposureBias = true;
    S.AutoExposureBias = -16;
    S.bOverride_IndirectLightingIntensity = true;
    S.IndirectLightingIntensity = 0;
    S.bOverride_BloomIntensity = true;
    S.BloomIntensity = 0;
}
