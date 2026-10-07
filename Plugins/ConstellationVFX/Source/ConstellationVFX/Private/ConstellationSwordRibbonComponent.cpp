#include "ConstellationSwordRibbonComponent.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Actor.h"
#include "Camera/PlayerCameraManager.h"
#include "Materials/MaterialInstanceDynamic.h"

UConstellationSwordRibbonComponent::UConstellationSwordRibbonComponent(const FObjectInitializer& ObjectInitializer) : Super(ObjectInitializer)
{
    SetCollisionEnabled(ECollisionEnabled::NoCollision);
    SetCastShadow(false);
    SetCanEverAffectNavigation(false);
}
void UConstellationSwordRibbonComponent::EnsureRibbonMesh()
{
    if (IsTemplate() || !GetOwner()) return;
    if (!IsValid(RibbonMesh))
    {
        RibbonMesh=NewObject<UProceduralMeshComponent>(GetOwner(),NAME_None,RF_Transient);
        RibbonMesh->SetupAttachment(this);
        RibbonMesh->SetRelativeTransform(FTransform::Identity);
        RibbonMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        RibbonMesh->SetCastShadow(false);
        RibbonMesh->SetCanEverAffectNavigation(false);
        RibbonMesh->SetMaterial(0,GetMaterial(0));
    }
    if (IsRegistered() && !RibbonMesh->IsRegistered()) RibbonMesh->RegisterComponent();
}
void UConstellationSwordRibbonComponent::OnRegister()
{
    // Old gallery maps can still contain the original plane and instance data.
    ClearInstances();
    SetStaticMesh(nullptr);
    Super::OnRegister();
    EnsureRibbonMesh();
}
void UConstellationSwordRibbonComponent::OnUnregister()
{
    if (IsValid(RibbonMesh) && RibbonMesh->IsRegistered()) RibbonMesh->UnregisterComponent();
    Super::OnUnregister();
}
void UConstellationSwordRibbonComponent::OnComponentDestroyed(bool bDestroyingHierarchy)
{
    if (IsValid(RibbonMesh)) RibbonMesh->DestroyComponent();
    RibbonMesh=nullptr;
    Super::OnComponentDestroyed(bDestroyingHierarchy);
}
FProcMeshSection* UConstellationSwordRibbonComponent::GetProcMeshSection(int32 SectionIndex) const
{
    return IsValid(RibbonMesh)?RibbonMesh->GetProcMeshSection(SectionIndex):nullptr;
}
void UConstellationSwordRibbonComponent::Configure(FLinearColor Color)
{
    if (auto* Material=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/Constellation/VFX/Materials/M_FX_SwordRibbon.M_FX_SwordRibbon")))
    {
        auto* Dynamic=UMaterialInstanceDynamic::Create(Material,this);
        Dynamic->SetVectorParameterValue(TEXT("Tint"),FLinearColor(Color.R*1.7f,Color.G*1.7f,Color.B*1.7f,Color.A));
        SetMaterial(0,Dynamic);
        EnsureRibbonMesh();
        if (RibbonMesh) RibbonMesh->SetMaterial(0,Dynamic);
    }
}
void UConstellationSwordRibbonComponent::ResetTrail()
{
    Samples.Reset();ActiveSegments=0;
    if (IsValid(RibbonMesh)) RibbonMesh->ClearAllMeshSections();
}
void UConstellationSwordRibbonComponent::AddTip(FVector WorldTip,float Delta)
{
    EnsureRibbonMesh();
    if (!IsValid(RibbonMesh)) return;
    constexpr float Lifetime=.18f;
    if (WorldTip.ContainsNaN() || !FMath::IsFinite(Delta) || Delta<0.f) { ResetTrail();return; }
    if (Delta>Lifetime || (!Samples.IsEmpty() && FVector::DistSquared(Samples.Last().Position,WorldTip)>FMath::Square(120.f))) ResetTrail();
    for (auto& Sample:Samples) Sample.Age+=Delta;
    Samples.RemoveAll([](const FTipSample& Sample){return Sample.Age>=.18f;});
    // Keep the same temporal history at high frame rates, capped at sixteen samples.
    if (Samples.IsEmpty() || (Samples.Last().Age>=.012f && FVector::DistSquared(Samples.Last().Position,WorldTip)>1.f))
    {
        if (Samples.Num()>=16) Samples.RemoveAt(0);
        Samples.Add({WorldTip,0.f});
    }
    ActiveSegments=FMath::Max(0,Samples.Num()-1);
    if (!ActiveSegments) { RibbonMesh->ClearAllMeshSections();return; }

    // Hermite interpolation rounds the sampled arc. Each cross-section is shared by
    // its two neighboring spans, including across original sample boundaries.
    constexpr int32 Subdivisions=4;
    TArray<FVector> Centers;
    TArray<float> Ages,Distances;
    for (int32 Span=0;Span<ActiveSegments;++Span)
    {
        const FVector P0=Samples[Span].Position,P1=Samples[Span+1].Position;
        const FVector T0=Span>0 ? (P1-Samples[Span-1].Position)*.5 : P1-P0;
        const FVector T1=Span+2<Samples.Num() ? (Samples[Span+2].Position-P0)*.5 : P1-P0;
        for (int32 Step=0;Step<Subdivisions;++Step)
        {
            const float T=float(Step)/Subdivisions;
            Centers.Add(FMath::CubicInterp(P0,T0,P1,T1,T));
            Ages.Add(FMath::Lerp(Samples[Span].Age,Samples[Span+1].Age,T));
        }
    }
    Centers.Add(Samples.Last().Position);Ages.Add(Samples.Last().Age);
    Distances.Add(0.f);
    for (int32 Index=1;Index<Centers.Num();++Index)
        Distances.Add(Distances.Last()+FVector::Distance(Centers[Index-1],Centers[Index]));

    const auto* PC=GetWorld()?GetWorld()->GetFirstPlayerController():nullptr;
    const auto* Camera=PC?PC->PlayerCameraManager.Get():nullptr;
    const FTransform ToWorld=GetComponentTransform();
    TArray<FVector> Vertices,Normals;
    TArray<FVector2D> UV;
    TArray<FLinearColor> Colors;
    TArray<FProcMeshTangent> Tangents;
    TArray<int32> Triangles;
    FVector PreviousSide=FVector::ZeroVector;
    for (int32 Index=0;Index<Centers.Num();++Index)
    {
        const FVector Travel=(Centers[FMath::Min(Index+1,Centers.Num()-1)]-Centers[FMath::Max(Index-1,0)]).GetSafeNormal();
        FVector Facing=Camera?(Camera->GetCameraLocation()-Centers[Index]).GetSafeNormal():FVector::UpVector;
        if (FMath::Abs(FVector::DotProduct(Travel,Facing))>.98f)
            Facing=FMath::Abs(Travel.Z)<.9f?FVector::UpVector:FVector::RightVector;
        FVector Side=FVector::CrossProduct(Facing,Travel).GetSafeNormal();
        if (FVector::DotProduct(Side,PreviousSide)<0.f) Side=-Side;
        PreviousSide=Side;
        const float Fade=FMath::Sqrt(FMath::Clamp(1.f-Ages[Index]/Lifetime,0.f,1.f));
        const float U=Distances[Index]/FMath::Max(Distances.Last(),UE_SMALL_NUMBER);
        for (int32 Edge=0;Edge<2;++Edge)
        {
            Vertices.Add(ToWorld.InverseTransformPosition(Centers[Index]+Side*((Edge?1.f:-1.f)*12.f*Fade)));
            Normals.Add(ToWorld.InverseTransformVectorNoScale(Facing));
            UV.Add(FVector2D(U,float(Edge)));
            Colors.Add(FLinearColor(1.f,1.f,1.f,Fade));
            Tangents.Add(FProcMeshTangent(ToWorld.InverseTransformVectorNoScale(Travel),false));
        }
        if (Index>0)
        {
            const int32 A=(Index-1)*2,B=Index*2;
            Triangles.Append({A,B,A+1,A+1,B,B+1});
        }
    }
    if (const FProcMeshSection* Section=GetProcMeshSection(0);Section && Section->ProcVertexBuffer.Num()==Vertices.Num())
        RibbonMesh->UpdateMeshSection_LinearColor(0,Vertices,Normals,UV,Colors,Tangents,false);
    else
        RibbonMesh->CreateMeshSection_LinearColor(0,Vertices,Triangles,Normals,UV,Colors,Tangents,false,false);
}
