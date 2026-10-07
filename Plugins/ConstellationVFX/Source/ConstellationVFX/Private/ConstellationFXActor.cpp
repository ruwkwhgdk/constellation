#include "ConstellationFXActor.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Engine/StaticMesh.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "Camera/PlayerCameraManager.h"
AConstellationFXActor::AConstellationFXActor() {
 PrimaryActorTick.bCanEverTick=true;SetActorEnableCollision(false);
 RootComponent=CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
 Shapes=CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("Shapes"));Shapes->SetupAttachment(RootComponent);
 Soft=CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("Soft"));Soft->SetupAttachment(RootComponent);
 ContactFlash=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ContactFlash"));ContactFlash->SetupAttachment(RootComponent);ContactFlash->SetCollisionEnabled(ECollisionEnabled::NoCollision);ContactFlash->SetCastShadow(false);ContactFlash->SetVisibility(false);
 for(auto* C:{Shapes.Get(),Soft.Get()}){C->SetCollisionEnabled(ECollisionEnabled::NoCollision);C->SetCastShadow(false);C->NumCustomDataFloats=1;C->SetReceivesDecals(false);}
}
void AConstellationFXActor::InitializeEffect(EConstellationFXKind Kind,FVector Direction,FLinearColor Color,float Scale) {
 LastEffectWorldTime=GetWorld()->GetTimeSeconds();
 ContactHold=Kind==EConstellationFXKind::PlayerHit?.065f:0.f;
 EffectKind=Kind;Age=0;Particles.Reset();Shapes->ClearInstances();Soft->ClearInstances();
 FVector Forward=Direction.GetSafeNormal();if(Forward.IsNearlyZero())Forward=FVector::UpVector;
 EffectDirection=Forward;
 const bool Combat=Kind==EConstellationFXKind::SwordHit||Kind==EConstellationFXKind::SwordBlock||Kind==EConstellationFXKind::SwordParry||Kind==EConstellationFXKind::PlayerHit||Kind==EConstellationFXKind::SlimeAttack||Kind==EConstellationFXKind::SlimeHit;
 bDirectionalFlash=Combat;
 Shapes->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Sphere.Sphere")));
 Soft->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Plane.Plane")));
 bool Gel=Kind==EConstellationFXKind::SlimeHit||Kind==EConstellationFXKind::SlimeAttack;
 bool Dust=Kind==EConstellationFXKind::RunDust||Kind==EConstellationFXKind::CaveDust||Kind==EConstellationFXKind::CaveMist;
 bool Glass=Kind==EConstellationFXKind::GlassBreak;
 if(Glass){auto* Shard=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/Constellation/VFX/Meshes/SM_GlassShard.SM_GlassShard"));Shapes->SetStaticMesh(Shard?Shard:LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube")));}
 const TCHAR* Material=Gel?TEXT("/Game/Constellation/VFX/Materials/M_FX_GelImpact.M_FX_GelImpact"):Glass?TEXT("/Game/Constellation/VFX/Materials/M_FX_Glass.M_FX_Glass"):Combat?TEXT("/Game/Constellation/VFX/Materials/M_FX_Impact.M_FX_Impact"):TEXT("/Game/Constellation/VFX/Materials/M_FX_Glow.M_FX_Glow");
 if(auto* M=LoadObject<UMaterialInterface>(nullptr,Material)){ShapeMaterial=UMaterialInstanceDynamic::Create(M,this);ShapeMaterial->SetVectorParameterValue(TEXT("Tint"),Color);Shapes->SetMaterial(0,ShapeMaterial);}
 const TCHAR* SoftPath=Combat?(Kind==EConstellationFXKind::PlayerHit||Kind==EConstellationFXKind::SwordBlock||Kind==EConstellationFXKind::SwordParry?TEXT("/Game/Constellation/VFX/Materials/M_FX_ImpactStar.M_FX_ImpactStar"):TEXT("/Game/Constellation/VFX/Materials/M_FX_Cut.M_FX_Cut")):Dust?TEXT("/Game/Constellation/VFX/Materials/M_FX_Dust.M_FX_Dust"):Kind==EConstellationFXKind::WaterRipple?TEXT("/Game/Constellation/VFX/Materials/M_FX_Ring.M_FX_Ring"):TEXT("/Game/Constellation/VFX/Materials/M_FX_Soft.M_FX_Soft");
 if(auto* M=LoadObject<UMaterialInterface>(nullptr,SoftPath)){SoftMaterial=UMaterialInstanceDynamic::Create(M,this);SoftMaterial->SetVectorParameterValue(TEXT("Tint"),Gel?FLinearColor(.65f,.45f,.9f,.9f):Color);if(Kind==EConstellationFXKind::WaterRipple)SoftMaterial->SetScalarParameterValue(TEXT("Brightness"),.25f);Soft->SetMaterial(0,SoftMaterial);}

 FHitResult Ground;FCollisionQueryParams Q(SCENE_QUERY_STAT(FXGround),false,this);
 GroundZ=GetActorLocation().Z-20;
 if(GetWorld()->LineTraceSingleByChannel(Ground,GetActorLocation()+FVector(0,0,10),GetActorLocation()-FVector(0,0,600),ECC_Visibility,Q))GroundZ=Ground.ImpactPoint.Z+1;
 if(Kind==EConstellationFXKind::PlayerHit){ContactFlash->SetStaticMesh(Soft->GetStaticMesh());ContactFlash->SetMaterial(0,SoftMaterial);ContactFlash->SetVisibility(true);}
 FRandomStream R(FMath::Rand());
 auto Add=[&](FVector Pos,FVector Vel,FVector Size,float Life,int32 Layer,float Gravity,float Growth,bool Billboard,bool Bounce){
  FConstellationFXParticle P;P.Position=Pos;P.Velocity=Vel*Scale;P.Size=Size*Scale*(Kind==EConstellationFXKind::RunDust?2.f:1.f);P.Life=Life;P.Layer=Layer;P.Gravity=Gravity;P.Growth=Growth;P.bBillboard=Billboard;P.bBounce=Bounce;
  P.bAlignVelocity=Combat&&Layer==0;P.Drag=Combat?(Gel?1.8f:4.f):0;
  P.Rotation=Layer==1?FRotator::ZeroRotator:FRotator(R.FRandRange(0,180),R.FRandRange(0,180),R.FRandRange(0,180));P.Spin=Layer==0?FRotator(R.FRandRange(-160,160),R.FRandRange(-180,180),R.FRandRange(-130,130)):FRotator::ZeroRotator;
  if(P.bAlignVelocity){P.Rotation=FRotationMatrix::MakeFromZ(P.Velocity.GetSafeNormal()).Rotator();P.Spin=FRotator::ZeroRotator;}
  if(Layer==2){Particles.Add(P);return;}
  P.Instance=(Layer==0?Shapes:Soft)->AddInstance(FTransform(P.Rotation,Pos,P.Size));(Layer==0?Shapes:Soft)->SetCustomDataValue(P.Instance,0,1,false);Particles.Add(P);
 };
 Duration=.6f;
 if(Gel){
  const bool Hit=Kind==EConstellationFXKind::SlimeHit;Duration=Hit?.68f:.42f;
  // A hit tears in the blade's travel direction; an attack releases a compact forward fan.
  const FVector Across=FVector::CrossProduct(Forward,FVector::UpVector).GetSafeNormal();
  const int Count=Hit?15:8;
  for(int I=0;I<Count;++I){
   const float S=I<3?R.FRandRange(.032f,.048f):R.FRandRange(.009f,.022f);
   const FVector V=Forward*R.FRandRange(Hit?170.f:100.f,Hit?380.f:210.f)+Across*R.FRandRange(-65,65)+FVector(0,0,R.FRandRange(20,100));
   Add(Forward*R.FRandRange(-7,7),V,FVector(S,S,Hit?S*R.FRandRange(2.5f,4.f):S*1.6f),R.FRandRange(Duration*.55f,Duration),0,520,0,false,false);
  }
  if(Hit){Add(FVector::ZeroVector,FVector::ZeroVector,FVector(.55,.19,.1),.12f,1,0,.25f,true,false);Add(Forward*5,Forward*30,FVector(.45,.12,.1),.18f,1,0,.7f,true,false);}
  else Add(FVector::ZeroVector,Forward*30,FVector(.3,.08,.1),.12f,1,0,.3f,true,false);
 }
 else if(Glass){Duration=3.2f;for(int32 I=0;I<38;++I){float S=R.FRandRange(.035,.15);Add(FVector(0,R.FRandRange(-35,35),R.FRandRange(-35,35))*Scale,Forward*R.FRandRange(90,330)+R.VRand()*R.FRandRange(40,210)+FVector(0,0,100),FVector(S,S*.8,S*.16),R.FRandRange(1.5,3.2),0,680,0,false,true);}}
 else if(Dust){bool Mist=Kind==EConstellationFXKind::CaveMist;bool Ambient=Kind==EConstellationFXKind::CaveDust;Duration=Mist?6.f:Ambient?4.f:1.05f;int32 Count=Mist?6:Ambient?12:7;for(int32 I=0;I<Count;++I){float S=Mist?R.FRandRange(3,5):Ambient?R.FRandRange(.015,.04):R.FRandRange(.14,.32);Add((Mist||Ambient)?FVector(R.FRandRange(-120,120),R.FRandRange(-120,120),R.FRandRange(0,80))*Scale:FVector(R.FRandRange(-6,6),R.FRandRange(-6,6),3),FVector(R.FRandRange(-12,12),R.FRandRange(-12,12),R.FRandRange(5,20)),FVector(S),Duration*R.FRandRange(.65,1),1,0,Mist?.2:Ambient?.1:1.8,true,false);}}
 else if(Kind==EConstellationFXKind::WaterDrop){Duration=1.4;for(int I=0;I<3;++I)Add(FVector(0,0,I*12),FVector(0,0,-160),FVector(.015,.015,.045),1.4,0,300,0,false,false);}
 else if(Kind==EConstellationFXKind::WaterRipple){Duration=1.6;Add(FVector(0,0,1),FVector::ZeroVector,FVector(.15),1.6,1,0,6,false,false);}
 else if(Kind==EConstellationFXKind::CaveSpore){Duration=5;for(int I=0;I<10;++I){float S=R.FRandRange(.025,.06);Add(FVector(R.FRandRange(-65,65),R.FRandRange(-65,65),R.FRandRange(0,70)),R.VRand()*8+FVector(0,0,9),FVector(S),R.FRandRange(3,5),1,0,0,true,false);}}
 else if(Kind==EConstellationFXKind::PlayerHit){
  Duration=.3f;
  // Contact-sized cut flash and a few flecks; no shield-like ring around the body.
  Add(FVector::ZeroVector,FVector::ZeroVector,FVector(.48,.48,.1),.14f,2,0,.25f,true,false);
  for(int I=0;I<6;++I)Add(FVector::ZeroVector,Forward*R.FRandRange(70,160)+R.VRand()*35,FVector(.006,.006,.045),R.FRandRange(.12,.28),0,180,0,false,false);
 }
 else {
  const bool Parry=Kind==EConstellationFXKind::SwordParry,Block=Kind==EConstellationFXKind::SwordBlock;
  Duration=Parry?.42f:Block?.32f:.24f;
  const int N=Parry?18:Block?11:5;
  for(int I=0;I<N;++I){
   FVector V=Forward*R.FRandRange(100,240)+R.VRand()*R.FRandRange(Block||Parry?90.f:20.f,Block||Parry?250.f:70.f);
   Add(FVector::ZeroVector,V,FVector(.004,.004,R.FRandRange(.035,.095)),R.FRandRange(.09,Duration),0,Block||Parry?330:130,0,false,false);
  }
  Add(FVector::ZeroVector,FVector::ZeroVector,Parry?FVector(.55,.55,.1):Block?FVector(.24,.24,.1):FVector(.42,.13,.1),Parry?.13f:.10f,1,0,.25f,true,false);
 }

 ParticleCount=Particles.Num();SetLifeSpan(Duration+.2f);AdvanceEffect(0);
}
void AConstellationFXActor::Tick(float Delta){
 Super::Tick(Delta);
 // A newly spawned actor must not consume time that elapsed before its contact event.
 const double Now=GetWorld()->GetTimeSeconds();
 const float Elapsed=FMath::Clamp(float(Now-LastEffectWorldTime),0.f,Delta);
 LastEffectWorldTime=Now;
 // Hold the impact's first pose briefly, then decay; total presentation remains bounded.
 if(ContactHold>0){ContactHold=FMath::Max(0.f,ContactHold-Elapsed);return;}
 AdvanceEffect(Elapsed);
}
void AConstellationFXActor::AdvanceEffect(float Delta){
 if(IsActorBeingDestroyed())return;
 Age+=Delta;if(Age>=Duration){Destroy();return;}
 auto* Camera=UGameplayStatics::GetPlayerCameraManager(this,0);
 for(auto& P:Particles){P.Age+=Delta;float T=FMath::Clamp(P.Age/P.Life,0.f,1.f);P.Velocity*=FMath::Exp(-P.Drag*Delta);P.Velocity.Z-=P.Gravity*Delta;P.Position+=P.Velocity*Delta;P.Rotation+=P.Spin*Delta;
  if(P.bBounce&&P.Position.Z+GetActorLocation().Z<GroundZ){P.Position.Z=GroundZ-GetActorLocation().Z;P.Velocity.Z=FMath::Abs(P.Velocity.Z)*.24;P.Velocity.X*=.65;P.Velocity.Y*=.65;P.Spin*=.5;}
  if(P.bAlignVelocity&&!P.Velocity.IsNearlyZero())P.Rotation=FRotationMatrix::MakeFromZ(P.Velocity.GetSafeNormal()).Rotator();
  if(P.bBillboard&&Camera){FVector To=Camera->GetCameraLocation()-(GetActorLocation()+P.Position);P.Rotation=bDirectionalFlash?FRotationMatrix::MakeFromZX(To,EffectDirection).Rotator():FRotationMatrix::MakeFromZ(To).Rotator();}
  FVector S=P.Size*(1+P.Growth*T);if(P.Layer==0&&!P.bBounce)S*=FMath::Max(.05f,1-T*.8f);if(T>=1)S=FVector::ZeroVector;
  if(P.Layer==2){ContactFlash->SetRelativeTransform(FTransform(P.Rotation,P.Position,S));ContactFlash->SetVisibility(T<1);if(SoftMaterial)SoftMaterial->SetScalarParameterValue(TEXT("EffectOpacity"),FMath::Pow(1-T,1.2f));continue;}
  auto* C=P.Layer==0?Shapes.Get():Soft.Get();C->UpdateInstanceTransform(P.Instance,FTransform(P.Rotation,P.Position,S),false,false,true);
  float Alpha=FMath::Pow(1-T,1.2f);if(EffectKind==EConstellationFXKind::CaveMist||EffectKind==EConstellationFXKind::CaveDust||EffectKind==EConstellationFXKind::CaveSpore)Alpha*=FMath::Clamp(P.Age/.6f,0.f,1.f);
  C->SetCustomDataValue(P.Instance,0,Alpha,false);
 }Shapes->MarkRenderInstancesDirty();Soft->MarkRenderInstancesDirty();
}
