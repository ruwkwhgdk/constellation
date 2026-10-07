#include "ResourceRecoveryLibrary.h"
#include "Animation/AnimationAsset.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimData/IAnimationDataController.h"
#include "Animation/Skeleton.h"
#include "Modules/ModuleManager.h"
#include "Engine/Blueprint.h"
#include "EdGraph/EdGraph.h"
#include "EdGraphUtilities.h"
#include "Engine/Level.h"
#include "Engine/LevelScriptBlueprint.h"
#include "Engine/World.h"
#include "Engine/TimelineTemplate.h"
#include "Curves/CurveFloat.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "Kismet2/CompilerResultsLog.h"
#include "Misc/Paths.h"
#include "Misc/PackageName.h"
#include "UObject/UObjectHash.h"
#include "UObject/CoreRedirects.h"

IMPLEMENT_MODULE(FDefaultModuleImpl, ConstellationResourceTools)

UBlueprint* UResourceRecoveryLibrary::LoadAuditAutosave(const FString& RelativeAutosavePath, const TMap<FString, FString>& PackageRedirects)
{
    FString Root = FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir() / TEXT("Autosaves"));
    FPaths::NormalizeDirectoryName(Root);
    FString Filename = FPaths::ConvertRelativePathToFull(Root / RelativeAutosavePath);
    FPaths::NormalizeFilename(Filename);
    FPaths::CollapseRelativeDirectories(Filename);
    if (!Filename.StartsWith(Root + TEXT("/")) || !FPaths::FileExists(Filename)) return nullptr;
    FPackageName::RegisterMountPoint(TEXT("/AuditAutosaves/"), Root + TEXT("/"));
    const FString PackageName = TEXT("/AuditAutosaves/") + FPaths::ChangeExtension(Filename.Mid(Root.Len() + 1), TEXT(""));
    TArray<FCoreRedirect> Redirects;
    for (const auto& Pair : PackageRedirects)
        Redirects.Emplace(ECoreRedirectFlags::Type_Package, Pair.Key, Pair.Value);
    FCoreRedirects::AddRedirectList(Redirects, TEXT("AuditAutosave"));
    UPackage* Package = LoadPackage(nullptr, *PackageName, LOAD_DisableCompileOnLoad);
    FCoreRedirects::RemoveRedirectList(Redirects, TEXT("AuditAutosave"));
    if (!Package) return nullptr;
    TArray<UObject*> Objects;
    GetObjectsWithOuter(Package, Objects, false);
    for (UObject* Object : Objects)
        if (UBlueprint* Blueprint = Cast<UBlueprint>(Object)) return Blueprint;
    return nullptr;
}

FString UResourceRecoveryLibrary::ExportBlueprintGraphs(UBlueprint* Blueprint)
{
    if (!IsValid(Blueprint)) return FString();
    FString Result;
    for (UTimelineTemplate* Timeline : Blueprint->Timelines)
    {
        if (!Timeline) continue;
        Result += FString::Printf(TEXT("TIMELINE %s length=%g\n"), *Timeline->GetName(), Timeline->TimelineLength);
        for (const FTTFloatTrack& Track : Timeline->FloatTracks)
        {
            Result += FString::Printf(TEXT("FLOAT_TRACK %s curve=%s external=%d\n"), *Track.GetTrackName().ToString(), *GetPathNameSafe(Track.CurveFloat), Track.bIsExternalCurve);
            if (Track.CurveFloat)
            {
                for (const FRichCurveKey& Key : Track.CurveFloat->FloatCurve.GetConstRefOfKeys())
                    Result += FString::Printf(TEXT("KEY time=%g value=%g interpolation=%d\n"), Key.Time, Key.Value, static_cast<int32>(Key.InterpMode));
            }
        }
    }
    TArray<UEdGraph*> Graphs;
    Blueprint->GetAllGraphs(Graphs);
    for (UEdGraph* Graph : Graphs)
    {
        if (!Graph) continue;
        Result += TEXT("\nGRAPH ") + Graph->GetPathName() + TEXT("\n");
        TSet<UObject*> Nodes;
        for (UEdGraphNode* Node : Graph->Nodes)
            if (Node) Nodes.Add(Node);
        FString Export;
        FEdGraphUtilities::ExportNodesToText(Nodes, Export);
        Result += Export;
    }
    return Result;
}

FString UResourceRecoveryLibrary::ExportLevelBlueprintGraphs(UWorld* World)
{
    if (!World || !World->PersistentLevel) return FString();
    ULevelScriptBlueprint* Blueprint = World->PersistentLevel->GetLevelScriptBlueprint(true);
    if (!Blueprint) return TEXT("NO_LEVEL_BLUEPRINT\n");
    FCompilerResultsLog Log;
    FKismetEditorUtilities::CompileBlueprint(Blueprint, EBlueprintCompileOptions::None, &Log);
    return FString::Printf(TEXT("COMPILE errors=%d warnings=%d\n"), Log.NumErrors, Log.NumWarnings) + ExportBlueprintGraphs(Blueprint);
}

bool UResourceRecoveryLibrary::RestoreMissingAnimationSkeleton(UAnimationAsset* Animation, USkeleton* Skeleton)
{
    if (!IsValid(Animation) || !IsValid(Skeleton))
    {
        return false;
    }
    if (Animation->GetSkeleton())
    {
        return Animation->GetSkeleton() == Skeleton;
    }
    Animation->Modify();
    Animation->SetSkeleton(Skeleton);
    if (UAnimSequence* Sequence = Cast<UAnimSequence>(Animation))
    {
        Sequence->GetController().UpdateWithSkeleton(Skeleton, false);
        Sequence->CacheDerivedDataForCurrentPlatform();
        Sequence->WaitOnExistingCompression();
    }
    Animation->PostEditChange();
    Animation->MarkPackageDirty();
    return Animation->GetSkeleton() == Skeleton;
}
