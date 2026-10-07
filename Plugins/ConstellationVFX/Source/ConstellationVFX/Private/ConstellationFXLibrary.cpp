#include "ConstellationFXLibrary.h"
#include "ConstellationFXActor.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
AConstellationFXActor* UConstellationFXLibrary::SpawnEffect(const UObject* Context,EConstellationFXKind Kind,FVector Location,FVector Direction,FLinearColor Color,float Scale) {
 UWorld* W=GEngine?GEngine->GetWorldFromContextObject(Context,EGetWorldErrorMode::ReturnNull):nullptr;
 if(!W||Location.ContainsNaN()||Direction.ContainsNaN()||!FMath::IsFinite(Scale)||Scale<=0||uint8(Kind)>uint8(EConstellationFXKind::PlayerHit))return nullptr;
 int32 Active=0;for(TActorIterator<AConstellationFXActor> It(W);It;++It)if(!It->IsActorBeingDestroyed())++Active;
 if(Active>=160)return nullptr;
 const FTransform Transform(FRotator::ZeroRotator,Location);
 // Register the short-lived primitive with populated geometry/materials and valid bounds.
 auto* FX=W->SpawnActorDeferred<AConstellationFXActor>(AConstellationFXActor::StaticClass(),Transform,nullptr,nullptr,ESpawnActorCollisionHandlingMethod::AlwaysSpawn);
 if(FX){FX->InitializeEffect(Kind,Direction,Color,FMath::Clamp(Scale,.05f,10.f));FX->FinishSpawning(Transform);}return FX;
}
void UConstellationFXLibrary::StopEffectsForOwner(AActor* Owner) {
 if(!IsValid(Owner)||!Owner->GetWorld())return;
 for(TActorIterator<AConstellationFXActor> It(Owner->GetWorld());It;++It)if(It->GetOwner()==Owner)It->Destroy();
}

#include "NiagaraSystem.h"
FString UConstellationFXLibrary::DescribeNiagara(UNiagaraSystem* S){FString Out;if(S){TArray<FNiagaraVariable> Vars;S->GetExposedParameters().GetUserParameters(Vars);for(const auto& V:Vars)Out+=V.GetName().ToString()+TEXT(" : ")+V.GetType().GetName()+TEXT("\n");}return Out;}

FLinearColor UConstellationFXLibrary::CombatColor(EConstellationFXKind Kind) {
 switch(Kind) {
 case EConstellationFXKind::SlimeAttack: case EConstellationFXKind::SlimeHit:return FLinearColor(.32f,.12f,.5f,1.f);
 case EConstellationFXKind::PlayerHit:return FLinearColor(.95f,.12f,.025f,1.f);
 case EConstellationFXKind::SwordBlock:return FLinearColor(1.f,.58f,.18f,1.f);
 case EConstellationFXKind::SwordParry:return FLinearColor(1.f,.82f,.43f,1.f);
 default:return FLinearColor(.8f,.88f,1.f,1.f);
 }
}
float UConstellationFXLibrary::CombatScale(EConstellationFXKind Kind) {
 switch(Kind){
 case EConstellationFXKind::SwordHit:return 2.4f;
 case EConstellationFXKind::SwordBlock:return 2.8f;
 case EConstellationFXKind::SwordParry:return 2.4f;
 case EConstellationFXKind::SlimeAttack:return 2.5f;
 case EConstellationFXKind::SlimeHit:return 2.3f;
 case EConstellationFXKind::PlayerHit:return 1.6f;
 default:return 1.f;
 }
}
