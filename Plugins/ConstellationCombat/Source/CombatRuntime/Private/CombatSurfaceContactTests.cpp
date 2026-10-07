#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "CombatSurfaceContact.h"
#include "CombatAbilitySystem.h"
#include "CombatActionDefinition.h"
#include "CombatLabCharacter.h"
#include "CombatVFXComponent.h"
#include "ConstellationFXActor.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Animation/AnimSequence.h"
namespace CombatTest
{
    UCombatActionDefinition* Action(UObject* Outer);
    ACombatLabCharacter* Actor(UWorld* World,FVector Location,int32 Team);
    int32 Instance(ACombatLabCharacter* Actor,UCombatActionDefinition* Action);
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatSurfaceTriangleTest,"Constellation.CombatVFX.Contact.PosedTriangle",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatSurfaceTriangleTest::RunTest(const FString&)
{
    // A sloped deformed body surface: its AABB face at X=10 is not its actual surface.
    const FVector Contact(10,0,5);
    FVector Position=Contact;
    double Distance=DBL_MAX;
    TestTrue(TEXT("Posed triangle is selected"),CombatSurfaceContact::ConsiderTriangle(Contact,
        FVector(0,-10,0),FVector(0,10,0),FVector(10,0,10),Distance,Position));
    TestTrue(TEXT("Closest point lies on sloped surface, not box face"),Position.Equals(FVector(7.5,0,7.5),.001));
    const FVector Selected=Position;
    TestFalse(TEXT("A farther triangle cannot replace contact"),CombatSurfaceContact::ConsiderTriangle(Contact,
        FVector(-100,-10,0),FVector(-100,10,0),FVector(-100,0,10),Distance,Position));
    TestEqual(TEXT("Nearest selection retained"),Position,Selected);
    TestFalse(TEXT("Degenerate geometry is ignored"),CombatSurfaceContact::ConsiderTriangle(Contact,
        Contact,Contact,Contact,Distance,Position));
    FVector Normal=FVector::UpVector; int32 Triangles=42;
    TestFalse(TEXT("Missing CPU mesh safely falls back"),CombatSurfaceContact::Resolve(nullptr,Contact,Normal,Position,Normal,Triangles));
    TestEqual(TEXT("Fallback leaves presentation point unchanged"),Position,Selected);
    TestEqual(TEXT("Fallback performs no triangle work"),Triangles,0);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatSlimeContactCueTest,"Constellation.CombatVFX.Contact.SlimeCustomCue",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatSlimeContactCueTest::RunTest(const FString&)
{
    auto* Asset=LoadObject<USkeletalMesh>(nullptr,TEXT("/Game/Constellation/Characters/Enemies/Slime_Normal/SKM_Slime_Normal.SKM_Slime_Normal"));
    auto* Idle=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/Constellation/Characters/Enemies/Slime_Normal/Animation/AS_Slime_Idle.AS_Slime_Idle"));
    if (!TestNotNull(TEXT("Maintained slime mesh"),Asset) || !TestNotNull(TEXT("Maintained idle pose"),Idle)) return false;
    auto* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Source=CombatTest::Actor(World,FVector(0,0,100),0);
    auto* Target=CombatTest::Actor(World,FVector(1000,0,100),1);
    Target->GetMesh()->SetSkeletalMeshAsset(Asset);
    Target->GetMesh()->PlayAnimation(Idle,true);
    Target->GetMesh()->TickAnimation(.4f,false);Target->GetMesh()->RefreshBoneTransforms();
    Target->CombatVFX->Style=ECombatVFXStyle::Slime;
    Source->CombatVFX->Style=ECombatVFXStyle::Sword;
    for (auto* Actor:{Source,Target}) { Actor->CombatVFX->SetPresentationEnabled(true);Actor->CombatVFX->Initialize(Actor->Combat); }
    Target->CombatVFX->HitCue.Mode=ECombatVFXCueMode::Builtin;
    Target->CombatVFX->HitCue.Kind=EConstellationFXKind::SwordParry;
    const FVector Contact=Target->GetActorLocation()+FVector(-34,0,0),Normal(-1,0,0);
    FVector Surface=Contact,SurfaceNormal=Normal;int32 Triangles=0;
    TestTrue(TEXT("Current slime resolves against CPU posed triangles"),CombatSurfaceContact::Resolve(Target->GetMesh(),Contact,Normal,Surface,SurfaceNormal,Triangles));
    TestTrue(TEXT("Hit query is bounded"),Triangles>0 && Triangles<=1024);
    FCombatConfirmedHit Observed;
    Source->Combat->OnHitConfirmed.AddLambda([&](const FCombatConfirmedHit& Hit){Observed=Hit;});
    auto* Action=CombatTest::Action(Source);
    Source->Combat->TryStartAction(Action);Source->Combat->OpenHitWindow("Swing",CombatTest::Instance(Source,Action));
    TestTrue(TEXT("Slime contact accepted"),Source->Combat->ApplyHit("Swing",Target,Contact,Normal));
    TestEqual(TEXT("Gameplay point unchanged"),Observed.Position,Contact);
    TestEqual(TEXT("Gameplay normal unchanged"),Observed.Normal,Normal);
    TestEqual(TEXT("Exactly one damage application"),Target->Combat->GetHealth(),80.f);
    AConstellationFXActor* Impact=nullptr;
    for (TActorIterator<AConstellationFXActor> It(World);It;++It)
        if (It->GetOwner()==Source && It->EffectKind==EConstellationFXKind::SwordParry && !It->IsActorBeingDestroyed()) Impact=*It;
    if (TestNotNull(TEXT("Custom cue emitted"),Impact))
        TestTrue(TEXT("Custom cue uses posed surface with two cm clearance"),Impact->GetActorLocation().Equals(Surface+SurfaceNormal*2.f,.01f));
    Source->Combat->CancelAction();World->DestroyWorld(false);return true;
}
#endif
