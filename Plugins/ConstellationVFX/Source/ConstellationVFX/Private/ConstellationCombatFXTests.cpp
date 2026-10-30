#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "ConstellationCombatFX.h"
#include "ConstellationSwordRibbonComponent.h"
#include "ConstellationFXActor.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Components/InstancedStaticMeshComponent.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatFXContactTest,"Constellation.VFX.CombatCandidates.ContactResults",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FCombatFXContactTest::RunTest(const FString&)
{
    UWorld* W=UWorld::CreateWorld(EWorldType::Game,false);
    auto Spawn=[&](EConstellationContactResult Result){return UConstellationCombatFX::SpawnContact(W,Result,EConstellationFXKind::SlimeHit,FVector::ZeroVector,FVector::ForwardVector);};
    TestNull(TEXT("A miss creates no contact effect"),Spawn(EConstellationContactResult::Miss));
    auto* Hit=Spawn(EConstellationContactResult::Hit);
    if(TestNotNull(TEXT("Accepted hit creates an effect"),Hit))
        TestEqual(TEXT("Target slime identity is retained"),Hit->EffectKind,EConstellationFXKind::SlimeHit);
    auto* Perfect=Spawn(EConstellationContactResult::PerfectGuard);
    if(TestNotNull(TEXT("Perfect creates one contact flash"),Perfect))
        TestEqual(TEXT("Perfect is not a damage hit"),Perfect->EffectKind,EConstellationFXKind::SwordParry);
    int32 Count=0;for(TActorIterator<AConstellationFXActor> I(W);I;++I)if(!I->IsActorBeingDestroyed())++Count;
    TestEqual(TEXT("No ordinary hit duplicated for perfect guard"),Count,2);
    W->DestroyWorld(false);return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatFXProfileTest,"Constellation.VFX.CombatCandidates.TrailProfiles",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FCombatFXProfileTest::RunTest(const FString&)
{
    UWorld* W=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Owner=W->SpawnActor<AActor>();
    auto* Ribbon=NewObject<UConstellationSwordRibbonComponent>(Owner);Ribbon->RegisterComponent();
    auto Width=[&](EConstellationAttackTrail Kind){
        UConstellationCombatFX::ConfigureTrail(Ribbon,Kind);
        Ribbon->AddTip(FVector::ZeroVector,0);Ribbon->AddTip(FVector(20,0,0),.03f);
        const auto* Section=Ribbon->GetProcMeshSection(0);
        if(!TestNotNull(TEXT("Each candidate generates real strip geometry"),Section) || Section->ProcVertexBuffer.Num()<2)return 0.f;
        return float(FVector::Distance(Section->ProcVertexBuffer.Last().Position,Section->ProcVertexBuffer[Section->ProcVertexBuffer.Num()-2].Position));
    };
    const float Light=Width(EConstellationAttackTrail::Light1);
    TestTrue(TEXT("Light finisher has a readable larger silhouette"),Width(EConstellationAttackTrail::Light3)>Light);
    TestTrue(TEXT("Second light candidate generates geometry"),Width(EConstellationAttackTrail::Light2)>0.f);
    TestTrue(TEXT("Heavy silhouette wider than light"),Width(EConstellationAttackTrail::Heavy1)>Light);
    TestTrue(TEXT("Heavy finisher is wider than heavy entry"),Width(EConstellationAttackTrail::Heavy2)>Width(EConstellationAttackTrail::Heavy1));
    const float LightParry=Width(EConstellationAttackTrail::LightParry);
    TestTrue(TEXT("Strong parry has its own silhouette"),Width(EConstellationAttackTrail::HeavyParry)>LightParry);
    Ribbon->ResetTrail();TestEqual(TEXT("Reset removes all trail spans"),Ribbon->GetSegmentCount(),0);
    W->DestroyWorld(false);return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatFXGroggyTest,"Constellation.VFX.CombatCandidates.GroggyLifecycle",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FCombatFXGroggyTest::RunTest(const FString&)
{
    UWorld* W=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Owner=W->SpawnActor<AActor>();
    auto* FX=NewObject<UConstellationGroggyFXComponent>(Owner);FX->RegisterComponent();
    FX->SetGroggy(true);FX->SetGroggy(true);
    int32 Hold=0,Enter=0;
    for(TActorIterator<AConstellationFXActor> I(W);I;++I)
    {
        Hold+=I->EffectKind==EConstellationFXKind::GroggyHold;Enter+=I->EffectKind==EConstellationFXKind::GroggyEnter;
        if(I->EffectKind==EConstellationFXKind::GroggyHold)
        {
            I->AdvanceEffect(30.f);
            TestFalse(TEXT("Hold survives long state duration"),I->IsActorBeingDestroyed());
            TestEqual(TEXT("Hold has a fixed six-particle budget"),I->ParticleCount,6);
            int32 Instances=0;
            TInlineComponentArray<UInstancedStaticMeshComponent*> Renderers(*I);
            for(auto* Renderer:Renderers)Instances+=Renderer->GetInstanceCount();
            TestEqual(TEXT("Actual render instances do not grow over long holds"),Instances,6);
        }
    }
    TestEqual(TEXT("Repeated state does not duplicate loop"),Hold,1);TestEqual(TEXT("Repeated state does not replay entry"),Enter,1);
    FX->SetGroggy(false);FX->SetGroggy(false);
    int32 Exit=0;for(TActorIterator<AConstellationFXActor> I(W);I;++I)if(!I->IsActorBeingDestroyed()){TestTrue(TEXT("Hold stops on exit"),I->EffectKind!=EConstellationFXKind::GroggyHold);Exit+=I->EffectKind==EConstellationFXKind::GroggyExit;}
    TestEqual(TEXT("One exit pulse per state change"),Exit,1);
    FX->SetGroggy(true);FX->StopPresentation();
    for(TActorIterator<AConstellationFXActor> I(W);I;++I)if(I->GetOwner()==Owner)TestTrue(TEXT("Death/reset clears all owned groggy effects"),I->IsActorBeingDestroyed());
    FX->SetGroggy(true);Owner->Destroy();
    for(TActorIterator<AConstellationFXActor> I(W);I;++I)if(I->EffectKind==EConstellationFXKind::GroggyHold && !I->IsActorBeingDestroyed())
    {
        I->Tick(.016f);TestTrue(TEXT("Destroyed owner cannot leave a persistent loop"),I->IsActorBeingDestroyed());
    }
    W->DestroyWorld(false);return true;
}
#endif
