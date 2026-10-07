#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "PhysicsPropComponent.h"
#include "HoldableComponent.h"
#include "CarryMath.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "PhysicalMaterials/PhysicalMaterial.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FPhysicsPropDataTest,"Constellation.PhysicsProps.InitialSettingsAndOwnership",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FPhysicsPropDataTest::RunTest(const FString&)
{
    TestTrue(TEXT("Chaos roundoff at lift boundary accepted"),CarryMath::CanLift(10.000001,50,.2));
    TestFalse(TEXT("Truly overweight rejected"),CarryMath::CanLift(10.01,50,.2));
    UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
    AActor* Actor=World->SpawnActor<AActor>();
    UStaticMeshComponent* Mesh=NewObject<UStaticMeshComponent>(Actor);
    Actor->SetRootComponent(Mesh);
    Mesh->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube")));
    Mesh->SetMobility(EComponentMobility::Movable);
    Mesh->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    Mesh->RegisterComponent();
    UPhysicsPropComponent* Physics=NewObject<UPhysicsPropComponent>(Actor);
    UDataTable* Table=NewObject<UDataTable>(); Table->RowStruct=FPhysicsPropRow::StaticStruct();
    FPhysicsPropRow Row; Row.MassKg=8; Row.LinearDamping=.8f; Row.AngularDamping=2;
    Row.bEnableGravity=false; Row.bSimulatePhysics=true;
    Row.PhysicalMaterial=NewObject<UPhysicalMaterial>();
    Table->AddRow(TEXT("Prop"),Row);
    Physics->PhysicsRow.DataTable=Table; Physics->PhysicsRow.RowName=TEXT("Prop");
    TestNull(TEXT("Physics works without holdable component"),Actor->FindComponentByClass<UHoldableComponent>());
    TestTrue(TEXT("Standalone prop settings apply"),Physics->ApplyInitialSettings());
    TestEqual(TEXT("Mass applied"),Mesh->GetMass(),8.f);
    TestEqual(TEXT("Linear damping applied"),Mesh->GetLinearDamping(),.8f);
    TestEqual(TEXT("Angular damping applied"),Mesh->GetAngularDamping(),2.f);
    TestFalse(TEXT("Gravity applied"),Mesh->IsGravityEnabled());
    TestTrue(TEXT("Physics applied"),Mesh->IsSimulatingPhysics());
    TestEqual(TEXT("Physical material applied"),Mesh->BodyInstance.GetSimplePhysicalMaterial(),Row.PhysicalMaterial.Get());
    Mesh->SetSimulatePhysics(false); Mesh->SetLinearDamping(0);
    TestFalse(TEXT("Cannot reapply over gameplay transitions"),Physics->ApplyInitialSettings());
    TestFalse(TEXT("Gameplay simulation preserved"),Mesh->IsSimulatingPhysics());
    TestEqual(TEXT("Gameplay damping preserved"),Mesh->GetLinearDamping(),0.f);
    UHoldableComponent* Hold=NewObject<UHoldableComponent>(Actor);
    TestEqual(TEXT("Lifting reads applied body mass"),Hold->GetWeightKg(),8.f);
    Mesh->SetMassOverrideInKg(NAME_None,12,true);
    TestEqual(TEXT("Lifting follows runtime mass changes"),Hold->GetWeightKg(),12.f);
    UPhysicsPropComponent* Invalid=NewObject<UPhysicsPropComponent>(Actor);
    Invalid->PhysicsRow=Physics->PhysicsRow;
    Row.MassKg=-1; Table->AddRow(TEXT("Prop"),Row);
    TestFalse(TEXT("Invalid mass rejected atomically"),Invalid->ApplyInitialSettings());
    TestEqual(TEXT("Invalid row does not change body"),Mesh->GetMass(),12.f);
    Mesh->SetSimulatePhysics(false);
    Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    TestEqual(TEXT("Held non-colliding prop retains throw weight"),Hold->GetWeightKg(),12.f);
    World->DestroyWorld(false);
    return true;
}
#endif
