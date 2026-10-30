#include "ConstellationMonsterTelegraphComponent.h"
#include "ProceduralMeshComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"
#include "GameFramework/Actor.h"
#include "GameFramework/PlayerController.h"
#include "Camera/PlayerCameraManager.h"
#include "Engine/World.h"

bool FMonsterTelegraphSettings::IsValid()const
{
    auto In=[](float V,float Min,float Max){return FMath::IsFinite(V) && V>=Min && V<=Max;};
    return In(Radius,4,500) && In(Thickness,1,Radius*.8f) && In(OutlineWidth,0,Thickness*.35f) &&
        In(Brightness,.1f,4) && In(CameraOffset,-100,100) && In(PreparationPulseAmount,0,.15f) &&
        In(PreparationPulseHz,0,4) && In(ExecutionFlashBoost,0,1) && In(ExecutionFlashDuration,0,1);
}
UConstellationMonsterTelegraphComponent::UConstellationMonsterTelegraphComponent()
{
    PrimaryComponentTick.bCanEverTick=true;
    PrimaryComponentTick.bStartWithTickEnabled=false;
    PrimaryComponentTick.TickGroup=TG_PostUpdateWork;
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> Material(TEXT("/Game/Constellation/VFX/Telegraph/M_MonsterTelegraph.M_MonsterTelegraph"));
    RingMaterial=Material.Object;
}
void UConstellationMonsterTelegraphComponent::OnRegister()
{
    Super::OnRegister();
    if(IsTemplate() || !GetOwner() || !GetWorld() || GetWorld()->GetNetMode()==NM_DedicatedServer)return;
    if(!Settings.IsValid())Settings=FMonsterTelegraphSettings();
    if(!IsValid(Ring))
    {
        Ring=NewObject<UProceduralMeshComponent>(GetOwner(),NAME_None,RF_Transient);
        Ring->SetupAttachment(this);Ring->SetAbsolute(false,true,true);
        Ring->SetCollisionEnabled(ECollisionEnabled::NoCollision);Ring->SetCastShadow(false);Ring->SetCanEverAffectNavigation(false);
        if(RingMaterial){DynamicMaterial=UMaterialInstanceDynamic::Create(RingMaterial,this);Ring->SetMaterial(0,DynamicMaterial);}
    }
    if(!Ring->IsRegistered())Ring->RegisterComponent();
    BuildRing();UpdatePresentation();
}
bool UConstellationMonsterTelegraphComponent::Configure(const FMonsterTelegraphSettings& NewSettings)
{
    if(!NewSettings.IsValid())return false;
    Settings=NewSettings;BuildRing();UpdatePresentation();return true;
}
bool UConstellationMonsterTelegraphComponent::SetAnchor(USceneComponent* Target,FName Socket,FVector LocalOffset)
{
    if(!IsValid(Target) || Target==this || Target->IsAttachedTo(this) || Target->GetOwner()!=GetOwner() || LocalOffset.ContainsNaN())return false;
    if(!Socket.IsNone() && !Target->DoesSocketExist(Socket))return false;
    auto* Previous=GetAttachParent();
    TGuardValue<bool> UpdatingAnchor(bUpdatingAnchor,true);
    if(!AttachToComponent(Target,FAttachmentTransformRules::SnapToTargetNotIncludingScale,Socket))return false;
    Anchor=Target;bHasAnchor=true;
    if(Previous)RemoveTickPrerequisiteComponent(Previous);
    AddTickPrerequisiteComponent(Target);SetRelativeLocation(LocalOffset);UpdatePresentation();return true;
}
bool UConstellationMonsterTelegraphComponent::BeginTelegraph(int64 AttackId)
{
    if(AttackId<=0 || !IsRegistered() || !IsValid(Ring) || !DynamicMaterial || !IsValid(GetOwner()) || GetOwner()->IsActorBeingDestroyed() || !IsAnchorAvailable())return false;
    if(AttackId==ActiveId)return true;
    if(AttackId<=LastId)return false;
    ActiveId=LastId=AttackId;Phase=EMonsterTelegraphPhase::Preparation;PhaseAge=0;
    SetComponentTickEnabled(true);UpdatePresentation();return true;
}
bool UConstellationMonsterTelegraphComponent::SetPhase(int64 AttackId,EMonsterTelegraphPhase NewPhase)
{
    if(AttackId<=0 || AttackId!=ActiveId || uint8(NewPhase)>uint8(EMonsterTelegraphPhase::Execution))return false;
    if(NewPhase==EMonsterTelegraphPhase::Hidden)return StopTelegraph(AttackId);
    if(Phase==NewPhase)return true;
    if(Phase==EMonsterTelegraphPhase::Execution)return false;
    Phase=NewPhase;PhaseAge=0;UpdatePresentation();return true;
}
bool UConstellationMonsterTelegraphComponent::StopTelegraph(int64 AttackId)
{
    if(AttackId<=0 || AttackId!=ActiveId)return false;
    StopAllTelegraphs();return true;
}
void UConstellationMonsterTelegraphComponent::StopAllTelegraphs()
{
    ActiveId=0;Phase=EMonsterTelegraphPhase::Hidden;PhaseAge=0;
    if(IsValid(Ring))Ring->SetVisibility(false);
    SetComponentTickEnabled(false);
}
bool UConstellationMonsterTelegraphComponent::IsShowingTelegraph()const
{
    return Phase!=EMonsterTelegraphPhase::Hidden && IsValid(Ring) && Ring->IsVisible();
}
void UConstellationMonsterTelegraphComponent::BuildRing()
{
    if(!IsValid(Ring))return;
    constexpr int32 Segments=96;
    const float Inner=Settings.Radius-Settings.Thickness*.5f,Outer=Settings.Radius+Settings.Thickness*.5f;
    const float Radii[]={Inner,Inner+Settings.OutlineWidth,Outer-Settings.OutlineWidth,Outer};
    TArray<FVector> Vertices,Normals;TArray<FVector2D> UV;TArray<int32> Triangles;
    TArray<FLinearColor> Colors;TArray<FProcMeshTangent> Tangents;
    for(int32 I=0;I<=Segments;++I)
    {
        const float Angle=2.f*PI*I/Segments;
        for(int32 Row=0;Row<4;++Row)
        {
            Vertices.Add(FVector(FMath::Cos(Angle)*Radii[Row],FMath::Sin(Angle)*Radii[Row],0));
            Normals.Add(FVector::UpVector);UV.Add(FVector2D(float(I)/Segments,float(Row)/3));
            const float Value=(Row==0 || Row==3)?.015f:1.f;
            Colors.Add(FLinearColor(Value,Value,Value,1));Tangents.Add(FProcMeshTangent(-FMath::Sin(Angle),FMath::Cos(Angle),0));
        }
        if(I<Segments)for(int32 Row=0;Row<3;++Row)
        {
            const int32 A=I*4+Row,B=(I+1)*4+Row;
            Triangles.Append({A,B,A+1,A+1,B,B+1});
        }
    }
    Ring->CreateMeshSection_LinearColor(0,Vertices,Triangles,Normals,UV,Colors,Tangents,false,false);
}
void UConstellationMonsterTelegraphComponent::UpdatePresentation()
{
    if(!IsValid(Ring))return;
    Ring->SetVisibility(Phase!=EMonsterTelegraphPhase::Hidden);
    FVector Position=GetComponentLocation();FQuat Rotation=GetComponentQuat();
    if(Settings.bFaceCamera && GetWorld())
        if(const auto* PC=GetWorld()->GetFirstPlayerController();PC && PC->PlayerCameraManager)
        {
            const FVector Facing=(PC->PlayerCameraManager->GetCameraLocation()-Position).GetSafeNormal();
            if(!Facing.IsNearlyZero()){Position+=Facing*Settings.CameraOffset;Rotation=FRotationMatrix::MakeFromZ(Facing).ToQuat();}
        }
    Ring->SetWorldLocationAndRotation(Position,Rotation);
    const bool Preparation=Phase==EMonsterTelegraphPhase::Preparation;
    const float Pulse=Preparation?Settings.PreparationPulseAmount*FMath::Sin(PhaseAge*Settings.PreparationPulseHz*2.f*PI):0.f;
    Ring->SetWorldScale3D(FVector(1.f+Pulse));
    if(DynamicMaterial)
    {
        DynamicMaterial->SetVectorParameterValue(TEXT("PhaseColor"),Preparation?FLinearColor(1.f,.82f,.01f,1.f):FLinearColor(1.f,.012f,.004f,1.f));
        const float Flash=Phase==EMonsterTelegraphPhase::Execution && Settings.ExecutionFlashDuration>0 ?
            Settings.ExecutionFlashBoost*FMath::Clamp(1.f-PhaseAge/Settings.ExecutionFlashDuration,0.f,1.f):0.f;
        DynamicMaterial->SetScalarParameterValue(TEXT("Brightness"),Settings.Brightness*(1.f+Flash));
    }
}
void UConstellationMonsterTelegraphComponent::TickComponent(float Delta,ELevelTick T,FActorComponentTickFunction* F)
{
    Super::TickComponent(Delta,T,F);
    if(!IsValid(GetOwner()) || GetOwner()->IsActorBeingDestroyed() || !IsAnchorAvailable()){StopAllTelegraphs();return;}
    if(Phase==EMonsterTelegraphPhase::Hidden || !FMath::IsFinite(Delta) || Delta<0)return;
    PhaseAge=FMath::Min(PhaseAge+Delta,3600.f);UpdatePresentation();
}
void UConstellationMonsterTelegraphComponent::OnUnregister()
{
    StopAllTelegraphs();if(IsValid(Ring) && Ring->IsRegistered())Ring->UnregisterComponent();Super::OnUnregister();
}
bool UConstellationMonsterTelegraphComponent::IsAnchorAvailable()const
{
    return !bHasAnchor || (Anchor.IsValid() && Anchor->IsRegistered() && GetAttachParent()==Anchor.Get());
}
void UConstellationMonsterTelegraphComponent::OnAttachmentChanged()
{
    Super::OnAttachmentChanged();
    if(!bUpdatingAnchor && !IsAnchorAvailable())StopAllTelegraphs();
}
void UConstellationMonsterTelegraphComponent::OnComponentDestroyed(bool B)
{
    StopAllTelegraphs();if(IsValid(Ring))Ring->DestroyComponent();Ring=nullptr;DynamicMaterial=nullptr;Super::OnComponentDestroyed(B);
}
void UConstellationMonsterTelegraphComponent::EndPlay(const EEndPlayReason::Type R)
{
    StopAllTelegraphs();Super::EndPlay(R);
}
