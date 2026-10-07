#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "ConstellationSwordRibbonComponent.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSwordRibbonMeshTest,"Constellation.VFX.SwordRibbon.ConnectedGeometry",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSwordRibbonMeshTest::RunTest(const FString&)
{
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    auto* Owner=World->SpawnActor<AActor>();
    auto* Ribbon=NewObject<UConstellationSwordRibbonComponent>(Owner);
    Ribbon->RegisterComponent();
    Ribbon->SetWorldTransform(FTransform(FRotator(10,30,0),FVector(200,-150,50),FVector(1.2)));
    for (int32 Index=0;Index<6;++Index)
        Ribbon->AddTip(FVector(Index*12,Index*Index*2,30),.016f);
    const FProcMeshSection* Section=Ribbon->GetProcMeshSection(0);
    if (TestNotNull(TEXT("Motion generates a procedural section"),Section))
    {
        const int32 CrossSections=Section->ProcVertexBuffer.Num()/2;
        TestTrue(TEXT("Curved history is smoothly tessellated"),CrossSections>Ribbon->GetSegmentCount()+1);
        TestEqual(TEXT("One pair of vertices per cross-section, with no disconnected quads"),Section->ProcIndexBuffer.Num(),(CrossSections-1)*6);
        TMap<uint64,int32> EdgeUses;
        for (int32 Triangle=0;Triangle<Section->ProcIndexBuffer.Num();Triangle+=3)
            for (int32 Edge=0;Edge<3;++Edge)
            {
                const uint32 A=Section->ProcIndexBuffer[Triangle+Edge],B=Section->ProcIndexBuffer[Triangle+(Edge+1)%3];
                TestTrue(TEXT("Every triangle index references a strip vertex"),A<uint32(Section->ProcVertexBuffer.Num()));
                ++EdgeUses.FindOrAdd((uint64(FMath::Min(A,B))<<32)|FMath::Max(A,B));
            }
        float PreviousU=-1.f;
        for (int32 Index=0;Index<CrossSections;++Index)
        {
            const auto& Left=Section->ProcVertexBuffer[Index*2];
            const auto& Right=Section->ProcVertexBuffer[Index*2+1];
            TestTrue(TEXT("Ribbon contains finite geometry"),!Left.Position.ContainsNaN() && !Right.Position.ContainsNaN());
            TestTrue(TEXT("UV runs continuously along the whole arc"),Left.UV0.X>=PreviousU && Left.UV0.X<=1.f);
            TestEqual(TEXT("Both edges share the same longitudinal UV"),Left.UV0.X,Right.UV0.X);
            if (Index>0 && Index<CrossSections-1)
                TestEqual(TEXT("Neighboring spans share the same edge indices"),EdgeUses.FindRef((uint64(Index*2)<<32)|uint32(Index*2+1)),2);
            PreviousU=Left.UV0.X;
        }
        TestTrue(TEXT("Old tail fades relative to fresh tip"),Section->ProcVertexBuffer[0].Color.A<Section->ProcVertexBuffer.Last().Color.A);
        const FVector TipCenter=(Section->ProcVertexBuffer[CrossSections*2-2].Position+Section->ProcVertexBuffer.Last().Position)*.5;
        TestTrue(TEXT("Mesh follows world-space tip under component transforms"),Ribbon->GetComponentTransform().TransformPosition(TipCenter).Equals(FVector(60,50,30),.001));
    }
    Ribbon->AddTip(FVector(60,50,30),.19f);
    TestTrue(TEXT("Expired trail clears its mesh"),!Ribbon->GetProcMeshSection(0) || Ribbon->GetProcMeshSection(0)->ProcVertexBuffer.IsEmpty());
    Ribbon->ResetTrail();
    TestEqual(TEXT("Reset clears logical spans"),Ribbon->GetSegmentCount(),0);
    World->DestroyWorld(false);
    return true;
}
#endif
