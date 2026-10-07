#include "ConstellationGlassRelay.h"
#include "ConstellationFXLibrary.h"
#include "ConstellationFXActor.h"
#include "GeometryCollection/GeometryCollectionComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "TimerManager.h"
AConstellationGlassRelay::AConstellationGlassRelay(){RootComponent=CreateDefaultSubobject<USceneComponent>(TEXT("Root"));}
void AConstellationGlassRelay::BeginPlay(){Super::BeginPlay();GetWorldTimerManager().SetTimer(BindTimer,this,&AConstellationGlassRelay::BindGlass,.5f,false);}
void AConstellationGlassRelay::BindGlass(){for(TActorIterator<AActor> It(GetWorld());It;++It){TInlineComponentArray<UGeometryCollectionComponent*> Parts(*It);for(auto* C:Parts){if(!C||(!C->GetName().Contains(TEXT("Glass"),ESearchCase::IgnoreCase)&&!It->GetClass()->GetName().Contains(TEXT("Glass"),ESearchCase::IgnoreCase)))continue;C->SetNotifyBreaks(true);C->OnChaosBreakEvent.AddUniqueDynamic(this,&AConstellationGlassRelay::OnGlassBreak);Collections.Add(C);}}BoundCollections=Collections.Num();}
void AConstellationGlassRelay::OnGlassBreak(const FChaosBreakEvent& E){double Now=GetWorld()->GetTimeSeconds();for(int I=LastTimes.Num()-1;I>=0;--I){if(Now-LastTimes[I]>.4){LastTimes.RemoveAtSwap(I);LastLocations.RemoveAtSwap(I);}else if(FVector::DistSquared(LastLocations[I],E.Location)<FMath::Square(200.f))return;}LastTimes.Add(Now);LastLocations.Add(E.Location);auto* FX=UConstellationFXLibrary::SpawnEffect(this,EConstellationFXKind::GlassBreak,E.Location,E.Velocity.GetSafeNormal(),FLinearColor(.65,.9,1,1),.55f);if(FX)FX->SetOwner(this);}
void AConstellationGlassRelay::EndPlay(const EEndPlayReason::Type R){GetWorldTimerManager().ClearTimer(BindTimer);for(auto C:Collections)if(C.IsValid())C->OnChaosBreakEvent.RemoveDynamic(this,&AConstellationGlassRelay::OnGlassBreak);UConstellationFXLibrary::StopEffectsForOwner(this);Super::EndPlay(R);}
