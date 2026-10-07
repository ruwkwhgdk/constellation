#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "CombatAbilitySystem.h"
#include "CombatActionDefinition.h"
#include "CombatLabCharacter.h"
#include "CombatVFXComponent.h"
#include "ConstellationFXActor.h"
#include "ConstellationSwordRibbonComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "NiagaraComponent.h"

// Reuse the maintained combat fixture without copying its montage/rig assumptions.
namespace CombatTest
{
    UCombatActionDefinition* Action(UObject* Outer);
    ACombatLabCharacter* Actor(UWorld* World,FVector Location,int32 Team);
    int32 Instance(ACombatLabCharacter* Actor,UCombatActionDefinition* Action);
}
namespace CombatPolishTest
{
    int32 Count(UWorld* World,AActor* Owner,EConstellationFXKind Kind)
    {
        int32 Result=0;
        for (TActorIterator<AConstellationFXActor> It(World);It;++It)
            if (!It->IsActorBeingDestroyed() && It->GetOwner()==Owner && It->EffectKind==Kind && !It->Tags.Contains(TEXT("CombatVFXWarmup"))) ++Result;
        return Result;
    }
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatVFXPolishTargetTest,"Constellation.CombatVFX.Polish.TargetMaterialAndSingleImpact",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatVFXPolishTargetTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Sword=CombatTest::Actor(World,FVector(0,0,100),0);
    auto* Slime=CombatTest::Actor(World,FVector(1000,0,100),1);
    Sword->CombatVFX->Style=ECombatVFXStyle::Sword;
    Slime->CombatVFX->Style=ECombatVFXStyle::Slime;
    for (auto* Actor:{Sword,Slime})
    { Actor->CombatVFX->SetPresentationEnabled(true);Actor->CombatVFX->Initialize(Actor->Combat); }
    auto* SwordAction=CombatTest::Action(Sword);
    TestTrue(TEXT("Sword action starts"),Sword->Combat->TryStartAction(SwordAction));
    Sword->Combat->OpenHitWindow("Swing",CombatTest::Instance(Sword,SwordAction));
    TInlineComponentArray<UNiagaraComponent*> Niagara(Sword);
    bool bActiveNiagara=false;for (auto* Component:Niagara) bActiveNiagara|=Component->IsActive();
    TestFalse(TEXT("Sword window does not also activate Niagara"),bActiveNiagara);
    FCombatConfirmedHit Recorded;
    Sword->Combat->OnHitConfirmed.AddLambda([&](const FCombatConfirmedHit& Hit){Recorded=Hit;});
    const FVector Contact(958,3,90);
    TestTrue(TEXT("Sword contact accepted"),Sword->Combat->ApplyHit("Swing",Slime,Contact,FVector(-1,0,0)));
    TestEqual(TEXT("Slime target emits one gel impact"),CombatPolishTest::Count(World,Sword,EConstellationFXKind::SlimeHit),1);
    TestEqual(TEXT("No duplicate white impact"),CombatPolishTest::Count(World,Sword,EConstellationFXKind::SwordHit),0);
    TestEqual(TEXT("Presentation leaves actual hit payload intact"),Recorded.Position,Contact);
    TestFalse(TEXT("Repeated contact rejected"),Sword->Combat->ApplyHit("Swing",Slime));
    TestEqual(TEXT("Repeated contact adds no gel impact"),CombatPolishTest::Count(World,Sword,EConstellationFXKind::SlimeHit),1);
    Sword->Combat->CancelAction();
    Slime->Combat->TickComponent(.5f,LEVELTICK_All,nullptr);
    auto* SlimeAction=CombatTest::Action(Slime);
    TestTrue(TEXT("Slime action starts after reaction"),Slime->Combat->TryStartAction(SlimeAction));
    Slime->Combat->OpenHitWindow("Swing",CombatTest::Instance(Slime,SlimeAction));
    TestTrue(TEXT("Slime contact accepted"),Slime->Combat->ApplyHit("Swing",Sword,FVector(42,0,100),FVector(1,0,0)));
    TestEqual(TEXT("Human target emits player impact"),CombatPolishTest::Count(World,Slime,EConstellationFXKind::PlayerHit),1);
    TestEqual(TEXT("Human target never emits slime droplets"),CombatPolishTest::Count(World,Slime,EConstellationFXKind::SlimeHit),0);
    Slime->Combat->CancelAction();World->DestroyWorld(false);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatVFXPolishRibbonTest,"Constellation.CombatVFX.Polish.RibbonContinuityAndLifetime",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatVFXPolishRibbonTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Owner=World->SpawnActor<AActor>();
    auto* Ribbon=NewObject<UConstellationSwordRibbonComponent>(Owner);
    Ribbon->Configure(FLinearColor(.8f,.88f,1.f,1.f));Ribbon->RegisterComponent();
    for(int32 Index=0;Index<100;++Index) Ribbon->AddTip(FVector(Index*2,0,0),.001f);
    TestTrue(TEXT("Motion creates a trail"),Ribbon->GetSegmentCount()>0);
    TestTrue(TEXT("High frame rate samples by time rather than consuming every slot"),Ribbon->GetSegmentCount()<12);
    TestTrue(TEXT("Trail retains at most sixteen points"),Ribbon->GetSegmentCount()<=15);
    Ribbon->AddTip(FVector(1000,0,0),.016f);
    TestEqual(TEXT("Teleport cannot draw a bridge"),Ribbon->GetSegmentCount(),0);
    Ribbon->AddTip(FVector(1002,0,0),.016f);
    TestEqual(TEXT("Motion resumes after teleport"),Ribbon->GetSegmentCount(),1);
    Ribbon->AddTip(FVector(1002,0,0),.19f);
    TestEqual(TEXT("Stationary trail expires after its readability window"),Ribbon->GetSegmentCount(),0);
    Ribbon->ResetTrail();TestEqual(TEXT("Reset removes all geometry"),Ribbon->GetSegmentCount(),0);
    World->DestroyWorld(false);return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatVFXAuthoredTest,"Constellation.CombatVFX.Authored.CharacterSlots",
 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatVFXAuthoredTest::RunTest(const FString&)
{
 auto* W=UWorld::CreateWorld(EWorldType::Game,false);
 auto* A=CombatTest::Actor(W,FVector(0,0,100),0);auto* B=CombatTest::Actor(W,FVector(1000,0,100),1);
 for(auto* C:{A,B}){C->CombatVFX->SetPresentationEnabled(true);C->CombatVFX->Initialize(C->Combat);}
 A->CombatVFX->AttackCue.Mode=ECombatVFXCueMode::Builtin;A->CombatVFX->AttackCue.Kind=EConstellationFXKind::SwordBlock;
 B->CombatVFX->HitCue.Mode=ECombatVFXCueMode::Builtin;B->CombatVFX->HitCue.Kind=EConstellationFXKind::SwordParry;
 auto* Action=CombatTest::Action(A);A->Combat->TryStartAction(Action);A->Combat->OpenHitWindow("Hit",CombatTest::Instance(A,Action));
 TestEqual(TEXT("Configured attack emitted"),CombatPolishTest::Count(W,A,EConstellationFXKind::SwordBlock),1);
 TestTrue(TEXT("Confirmed hit accepted"),A->Combat->ApplyHit("Hit",B));
 TestEqual(TEXT("Target chooses hit effect"),CombatPolishTest::Count(W,A,EConstellationFXKind::SwordParry),1);
 TestFalse(TEXT("Duplicate hit rejected"),A->Combat->ApplyHit("Hit",B));
 TestEqual(TEXT("No duplicate authored impact"),CombatPolishTest::Count(W,A,EConstellationFXKind::SwordParry),1);
 A->Combat->CancelAction();TestFalse(TEXT("Attack effect retired on cancel"),A->CombatVFX->HasAttackPresentation());
 TestEqual(TEXT("Cancelled attack removed"),CombatPolishTest::Count(W,A,EConstellationFXKind::SwordBlock),0);
 A->CombatVFX->StopPresentation();B->CombatVFX->HitCue.Mode=ECombatVFXCueMode::Disabled;
 FCombatConfirmedHit Hit;Hit.Source=A;Hit.Target=B;Hit.Position=B->GetActorLocation();Hit.Normal=FVector::UpVector;
 A->Combat->OnHitConfirmed.Broadcast(Hit);
 TestEqual(TEXT("Disabled target hit suppresses effect"),CombatPolishTest::Count(W,A,EConstellationFXKind::SwordParry),0);
 B->CombatVFX->HitCue.Mode=ECombatVFXCueMode::Builtin;B->CombatVFX->SetPresentationEnabled(false);
 A->Combat->OnHitConfirmed.Broadcast(Hit);
 TestEqual(TEXT("Disabled receiver suppresses impact"),CombatPolishTest::Count(W,A,EConstellationFXKind::SwordParry),0);
 A->CombatVFX->SetPresentationEnabled(false);B->CombatVFX->SetPresentationEnabled(true);
 A->Combat->OnHitConfirmed.Broadcast(Hit);
 TestEqual(TEXT("Receiver impact independent of attacker display"),CombatPolishTest::Count(W,A,EConstellationFXKind::SwordParry),1);
 W->DestroyWorld(false);return true;
}
#endif
