#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "ConstellationFXLibrary.h"
#include "ConstellationFXActor.generated.h"
class UInstancedStaticMeshComponent;
class UMaterialInstanceDynamic;
class UStaticMeshComponent;
USTRUCT()
struct FConstellationFXParticle {
 GENERATED_BODY()
 FVector Position=FVector::ZeroVector, Velocity=FVector::ZeroVector, Size=FVector::OneVector;
 FRotator Rotation=FRotator::ZeroRotator, Spin=FRotator::ZeroRotator;
 float Life=1,Age=0,Gravity=0,Growth=0;
 int32 Instance=INDEX_NONE,Layer=0;
 bool bBillboard=false,bBounce=false,bAlignVelocity=false;
 float Drag=0;
};
UCLASS(BlueprintType)
class CONSTELLATIONVFX_API AConstellationFXActor : public AActor {
 GENERATED_BODY()
public:
 AConstellationFXActor();
 void InitializeEffect(EConstellationFXKind Kind,FVector Direction,FLinearColor Color,float Scale);
 virtual void Tick(float DeltaSeconds) override;
 void AdvanceEffect(float DeltaSeconds);
 UFUNCTION() void OnSceneStopped(bool bCompleted) { Destroy(); }
 float GetDuration() const {return Duration;}
 UPROPERTY(BlueprintReadOnly,Category="Effects") EConstellationFXKind EffectKind=EConstellationFXKind::SwordHit;
 UPROPERTY(BlueprintReadOnly,Category="Effects") int32 ParticleCount=0;
private:
 UPROPERTY() TObjectPtr<UInstancedStaticMeshComponent> Shapes;
 UPROPERTY() TObjectPtr<UInstancedStaticMeshComponent> Soft;
 UPROPERTY() TObjectPtr<UStaticMeshComponent> ContactFlash;
 UPROPERTY() TObjectPtr<UMaterialInstanceDynamic> ShapeMaterial;
 UPROPERTY() TObjectPtr<UMaterialInstanceDynamic> SoftMaterial;
 TArray<FConstellationFXParticle> Particles;
 float Duration=1,Age=0,GroundZ=0,ContactHold=0;
 double LastEffectWorldTime=0;
 FVector EffectDirection=FVector::ForwardVector;
 bool bDirectionalFlash=false;
};
