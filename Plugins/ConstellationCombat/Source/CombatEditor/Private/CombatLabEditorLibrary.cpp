#include "CombatLabEditorLibrary.h"
#include "CombatHitWindow.h"
#include "Animation/AnimMontage.h"
#include "Modules/ModuleManager.h"

bool UCombatLabEditorLibrary::ConfigureReviewMontage(UAnimMontage* Montage, float Start, float End)
{
    if (!Montage || !Montage->GetOutermost()->GetName().StartsWith(TEXT("/Game/Constellation/Review/CombatCore/")) ||
        !FMath::IsFinite(Start) || !FMath::IsFinite(End) || Start < 0 || End <= Start || End > Montage->GetPlayLength()) return false;
    Montage->Modify();
    Montage->Notifies.Reset();
    UCombatHitWindow* Window = NewObject<UCombatHitWindow>(Montage);
    FAnimNotifyEvent Event;
    Event.NotifyStateClass = Window; Event.NotifyName = TEXT("CombatHit");
    Event.Link(Montage, Start); Event.SetDuration(End - Start); Event.EndLink.Link(Montage, End);
    Montage->Notifies.Add(Event);
    Montage->MarkPackageDirty(); return true;
}

#include "Engine/World.h"
#include "EngineUtils.h"
#include "NavMesh/NavMeshBoundsVolume.h"
#include "NavigationSystem.h"
#include "NavigationData.h"
#include "AssetCompilingManager.h"
#include "ActorFactories/ActorFactory.h"
#include "Builders/CubeBuilder.h"
bool UCombatLabEditorLibrary::BuildEncounterNavigation(UObject* WorldContext)
{
    UWorld* World=WorldContext?WorldContext->GetWorld():nullptr;
    if(!World || World->GetOutermost()->GetName()!=TEXT("/Game/Constellation/Review/CombatCore/L_CombatEncounter")) return false;
    ANavMeshBoundsVolume* Volume=nullptr;
    for(TActorIterator<ANavMeshBoundsVolume> It(World);It;++It) { Volume=*It; break; }
    if(!Volume)
    {
        Volume=World->SpawnActor<ANavMeshBoundsVolume>();
        auto* Builder=NewObject<UCubeBuilder>(); Builder->X=1900; Builder->Y=1900; Builder->Z=600;
        UActorFactory::CreateBrushForVolumeActor(Volume,Builder);
        Volume->SetActorLocation(FVector(0,0,100)); Volume->SetActorLabel(TEXT("Combat Encounter Nav Bounds"));
        Volume->MarkPackageDirty();
    }
    auto* Nav=FNavigationSystem::GetCurrent<UNavigationSystemV1>(World);
    if(!Nav) return false;
    // Commandlets do not tick the delayed async-load unlock while this script runs.
    FlushAsyncLoading(); FAssetCompilingManager::Get().FinishAllCompilation();
    Nav->RemoveNavigationBuildLock(ENavigationBuildLock::AsyncLoadLock, UNavigationSystemV1::ELockRemovalRebuildAction::NoRebuild);
    Nav->OnNavigationBoundsUpdated(Volume); Nav->Build();
    if(auto* Data=Nav->GetDefaultNavDataInstance(FNavigationSystem::Create)) Data->EnsureBuildCompletion();
    FNavLocation Projected;
    return Nav->ProjectPointToNavigation(FVector(-500,0,0),Projected,FVector(100,100,200));
}



#include "CombatActionDefinition.h"
#include "CombatPatternProfile.h"
#include "CombatEncounterProfile.h"
FString UCombatLabEditorLibrary::GetCombatAssetError(UObject* Asset)
{
    FString Reason;
    if(auto* Action=Cast<UCombatActionDefinition>(Asset)) Action->Validate(Reason);
    else if(auto* Patterns=Cast<UCombatPatternProfile>(Asset)) Patterns->Validate(Reason);
    else if(auto* Encounter=Cast<UCombatEncounterProfile>(Asset)) Encounter->Validate(Reason);
    else Reason=TEXT("Unsupported combat asset type");
    return Reason;
}

bool UCombatLabEditorLibrary::ConfigureAuthoredHitWindows(UAnimMontage* Montage, const TArray<FName>& Ids, const TArray<float>& Starts, const TArray<float>& Ends)
{
    if(!Montage || (Montage->GetOutermost()!=GetTransientPackage() && !Montage->GetOutermost()->GetName().StartsWith(TEXT("/Game/Constellation/Review/CombatRecipes/"))) ||
        Ids.IsEmpty() || Ids.Num()>32 || Starts.Num()!=Ids.Num() || Ends.Num()!=Ids.Num()) return false;
    TSet<FName> Seen;
    for(int32 I=0;I<Ids.Num();++I)
    {
        if(Ids[I].IsNone() || Seen.Contains(Ids[I]) || !FMath::IsFinite(Starts[I]) || !FMath::IsFinite(Ends[I]) ||
            Starts[I]<0 || Ends[I]<=Starts[I] || Ends[I]>Montage->GetPlayLength()) return false;
        Seen.Add(Ids[I]);
    }
    Montage->Modify();
    Montage->Notifies.RemoveAll([](const FAnimNotifyEvent& E){return Cast<UCombatHitWindow>(E.NotifyStateClass)!=nullptr;});
    for(int32 I=0;I<Ids.Num();++I)
    {
        auto* Window=NewObject<UCombatHitWindow>(Montage);Window->WindowId=Ids[I];
        FAnimNotifyEvent Event;Event.NotifyStateClass=Window;Event.NotifyName=Ids[I];
        Event.Link(Montage,Starts[I]);Event.SetDuration(Ends[I]-Starts[I]);Event.EndLink.Link(Montage,Ends[I]);
        Montage->Notifies.Add(Event);
    }
    Montage->MarkPackageDirty();return true;
}

UAnimMontage* UCombatLabEditorLibrary::PreviewAuthoredHitWindows(UAnimMontage* Source,const TArray<FName>& Ids,const TArray<float>& Starts,const TArray<float>& Ends)
{
    if(!Source) return nullptr;
    auto* Copy=DuplicateObject<UAnimMontage>(Source,GetTransientPackage());
    return ConfigureAuthoredHitWindows(Copy,Ids,Starts,Ends)?Copy:nullptr;
}

#include "CombatLabCharacter.h"
ACombatLabCharacter* UCombatLabEditorLibrary::DuplicateReviewEnemy(ACombatLabCharacter* Source,FVector Offset)
{
    if(!Source || !Source->bTrainingEnemy || Offset.ContainsNaN() || Offset.GetAbsMax()>10000) return nullptr;
    auto* World=Source->GetWorld();
    if(!World || !World->GetOutermost()->GetName().StartsWith(TEXT("/Game/Constellation/Review/"))) return nullptr;
    // EditorActorSubsystem duplication routes through GUnrealEd, absent in a Python commandlet.
    FActorSpawnParameters Params;Params.Template=Source;
    Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    auto* Copy=World->SpawnActor<ACombatLabCharacter>(Source->GetClass(),Source->GetActorLocation()+Offset,Source->GetActorRotation(),Params);
    if(Copy) Copy->MarkPackageDirty();
    return Copy;
}
