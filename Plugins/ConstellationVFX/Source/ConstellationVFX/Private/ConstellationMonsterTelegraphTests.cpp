#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "ConstellationMonsterTelegraphComponent.h"
#include "ProceduralMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "Materials/MaterialInstanceDynamic.h"
#include <limits>

namespace TelegraphTest
{
    struct FWorld
    {
        UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
        FWorld(){GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);}
        ~FWorld(){World->DestroyWorld(false);GEngine->DestroyWorldContext(World);}
        UConstellationMonsterTelegraphComponent* Create()
        {
            auto* A=World->SpawnActor<AActor>();
            auto* C=NewObject<UConstellationMonsterTelegraphComponent>(A);A->SetRootComponent(C);C->RegisterComponent();return C;
        }
    };
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FTelegraphLifecycleTest,"Constellation.VFX.Telegraph.Lifecycle",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FTelegraphLifecycleTest::RunTest(const FString&)
{
    TelegraphTest::FWorld W;auto* C=W.Create();auto* Other=W.Create();
    TestFalse(TEXT("Starts hidden"),C->IsShowingTelegraph());
    TestTrue(TEXT("Begins preparation"),C->BeginTelegraph(1));
    auto* Ring=C->GetOwner()->FindComponentByClass<UProceduralMeshComponent>();
    auto* Material=Ring?Cast<UMaterialInstanceDynamic>(Ring->GetMaterial(0)):nullptr;
    if(TestNotNull(TEXT("Reusable telegraph material is loaded"),Material))
    {
        const auto Yellow=Material->K2_GetVectorParameterValue(TEXT("PhaseColor"));
        TestTrue(TEXT("Preparation is yellow"),Yellow.R>.9f && Yellow.G>.7f && Yellow.B<.1f);
    }
    C->TickComponent(60.f,LEVELTICK_All,nullptr);
    TestEqual(TEXT("Time alone never advances to execution"),C->GetPhase(),EMonsterTelegraphPhase::Preparation);
    TestTrue(TEXT("Explicit execution event switches phase"),C->SetPhase(1,EMonsterTelegraphPhase::Execution));
    if(Material)
    {
        const auto Red=Material->K2_GetVectorParameterValue(TEXT("PhaseColor"));
        TestTrue(TEXT("Execution is red"),Red.R>.9f && Red.G<.1f && Red.B<.1f);
    }
    TestFalse(TEXT("Same attack cannot return to preparation"),C->SetPhase(1,EMonsterTelegraphPhase::Preparation));
    TestTrue(TEXT("Duplicate begin is idempotent"),C->BeginTelegraph(1));
    TestEqual(TEXT("Duplicate begin does not reset execution"),C->GetPhase(),EMonsterTelegraphPhase::Execution);
    Other->BeginTelegraph(1);C->BeginTelegraph(2);
    TestFalse(TEXT("Old execution cannot turn new preparation red"),C->SetPhase(1,EMonsterTelegraphPhase::Execution));
    TestFalse(TEXT("Old stop cannot clear new attack"),C->StopTelegraph(1));
    TestTrue(TEXT("Current stop accepted"),C->StopTelegraph(2));
    TestFalse(TEXT("Stop hides immediately"),C->IsShowingTelegraph());
    TestFalse(TEXT("Cancelled attack cannot revive"),C->BeginTelegraph(2));
    TestTrue(TEXT("Other enemy remains visible"),Other->IsShowingTelegraph());
    Other->StopAllTelegraphs();TestFalse(TEXT("Reset clears the other enemy"),Other->IsShowingTelegraph());
    TestFalse(TEXT("Invalid zero ID rejected"),C->BeginTelegraph(0));
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FTelegraphGeometryTest,"Constellation.VFX.Telegraph.HollowGeometry",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FTelegraphGeometryTest::RunTest(const FString&)
{
    TelegraphTest::FWorld W;auto* C=W.Create();C->BeginTelegraph(1);
    auto* Mesh=C->GetOwner()->FindComponentByClass<UProceduralMeshComponent>();
    if(!TestNotNull(TEXT("A real annulus mesh is registered"),Mesh))return false;
    const auto* Section=Mesh->GetProcMeshSection(0);if(!TestNotNull(TEXT("Ring geometry exists"),Section))return false;
    const float Inner=C->Settings.Radius-C->Settings.Thickness*.5f;
    for(const auto& V:Section->ProcVertexBuffer)TestTrue(TEXT("Center contains no vertices"),V.Position.Size()>=Inner-.01f);
    for(int32 I=0;I<Section->ProcIndexBuffer.Num();I+=3)
    {
        const auto A=Section->ProcVertexBuffer[Section->ProcIndexBuffer[I]].Position;
        const auto B=Section->ProcVertexBuffer[Section->ProcIndexBuffer[I+1]].Position;
        const auto D=Section->ProcVertexBuffer[Section->ProcIndexBuffer[I+2]].Position;
        // Every triangle is confined to a small angular sector, never crossing the hole.
        TestTrue(TEXT("No triangle spans the center"),FVector::DotProduct(A,B)>0 && FVector::DotProduct(B,D)>0 && FVector::DotProduct(D,A)>0);
    }
    const int32 Vertices=Section->ProcVertexBuffer.Num();
    for(int32 I=0;I<100;++I)C->TickComponent(.033f,LEVELTICK_All,nullptr);
    TestEqual(TEXT("Pulse does not allocate growing geometry"),Mesh->GetProcMeshSection(0)->ProcVertexBuffer.Num(),Vertices);
    FMonsterTelegraphSettings Bad=C->Settings;Bad.Thickness=Bad.Radius*3;
    TestFalse(TEXT("Configuration cannot close the hole"),C->Configure(Bad));
    TestEqual(TEXT("Rejected configuration is atomic"),C->Settings.Thickness,8.f);
    auto Good=C->Settings;Good.Radius=80;Good.Thickness=12;Good.PreparationPulseAmount=0;Good.ExecutionFlashBoost=0;
    TestTrue(TEXT("Size and motion can be configured"),C->Configure(Good));
    TestEqual(TEXT("Configured radius retained"),C->Settings.Radius,80.f);
    return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FTelegraphAttachmentTest,"Constellation.VFX.Telegraph.AttachmentAndReregister",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FTelegraphAttachmentTest::RunTest(const FString&)
{
    TelegraphTest::FWorld W;
    auto* Actor=W.World->SpawnActor<AActor>();
    auto* Anchor=NewObject<USceneComponent>(Actor);Actor->SetRootComponent(Anchor);Anchor->RegisterComponent();
    auto* C=NewObject<UConstellationMonsterTelegraphComponent>(Actor);C->RegisterComponent();
    TestTrue(TEXT("Attach to owned anchor"),C->SetAnchor(Anchor,NAME_None,FVector(0,0,45)));
    Anchor->SetWorldLocation(FVector(100,200,300));C->BeginTelegraph(1);C->TickComponent(.016f,LEVELTICK_All,nullptr);
    TestTrue(TEXT("Anchor motion preserves the local attachment point"),C->GetComponentLocation().Equals(FVector(100,200,345),.01));
    auto Bad=C->Settings;Bad.Brightness=std::numeric_limits<float>::infinity();
    TestFalse(TEXT("Nonfinite settings rejected"),C->Configure(Bad));
    TestFalse(TEXT("Cannot attach to another enemy"),C->SetAnchor(W.Create(),NAME_None,FVector::ZeroVector));
    C->UnregisterComponent();C->RegisterComponent();
    TestFalse(TEXT("Reregister does not restore stale attack"),C->IsShowingTelegraph());
    TestFalse(TEXT("Old callback cannot restore after reregister"),C->SetPhase(1,EMonsterTelegraphPhase::Execution));
    C->BeginTelegraph(2);Anchor->DestroyComponent();
    TestFalse(TEXT("Attachment removal clears even without another tick"),C->IsShowingTelegraph());
    C->TickComponent(.016f,LEVELTICK_All,nullptr);
    TestFalse(TEXT("Removing the attachment target clears the ring"),C->IsShowingTelegraph());
    TestFalse(TEXT("Cannot begin against a removed attachment target"),C->BeginTelegraph(3));
    return true;
}
#endif
