#include "CarryEditorLibrary.h"
#include "Engine/SkeletalMesh.h"
#include "Animation/MorphTarget.h"
#include "Rendering/SkeletalMeshModel.h"
#include "Rendering/SkeletalMeshLODModel.h"
#include "Misc/FileHelper.h"
#include "Serialization/JsonSerializer.h"
#include "SkeletalMeshAttributes.h"
#include "MeshDescription.h"
#include "SkinnedAssetCompiler.h"

FString UCarryEditorLibrary::ImportCarryMorphs(USkeletalMesh* Mesh,const FString& JsonPath)
{
    FString Text; TSharedPtr<FJsonObject> Root;
    if(!Mesh||!FFileHelper::LoadFileToString(Text,*JsonPath)||!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Root)) return TEXT("ERROR input");
    FMeshDescription* Description=Mesh->GetMeshDescription(0);
    if(!Description) return TEXT("ERROR no mesh description");
    FSkeletalMeshAttributes Attributes(*Description);
    const auto VertexPositions=Attributes.GetVertexPositions();
    constexpr float Cell=.01f;
    auto Grid=[](const FVector3f& P){ return FIntVector(FMath::FloorToInt(P.X/Cell),FMath::FloorToInt(P.Y/Cell),FMath::FloorToInt(P.Z/Cell)); };
    TMap<FIntVector,TArray<TPair<uint32,FVector3f>>> Positions;
    for(const FVertexID Vertex:Description->Vertices().GetElementIDs())
    { const FVector3f P=VertexPositions[Vertex]; Positions.FindOrAdd(Grid(P)).Emplace(Vertex.GetValue(),P); }
    TMap<FString,TArray<FMorphTargetDelta>> Prepared; int32 Count=0;
    for(const auto& Pair:Root->Values)
    {
        const FString Name(*Pair.Key);
        if(!Name.StartsWith(TEXT("PutDown_Chair_"))&&!Name.StartsWith(TEXT("PutDown_Desk_"))) return TEXT("ERROR unexpected morph name");
        TMap<uint32,FMorphTargetDelta> Unique;
        for(const auto& Value:Pair.Value->AsArray())
        {
            const auto Object=Value->AsObject(); const auto& P=Object->GetArrayField(TEXT("p")); const auto& D=Object->GetArrayField(TEXT("d"));
            const FVector3f Pos(P[0]->AsNumber(),P[1]->AsNumber(),P[2]->AsNumber());
            const FVector3f Delta(D[0]->AsNumber(),D[1]->AsNumber(),D[2]->AsNumber());
            const FIntVector G=Grid(Pos); bool Found=false;
            for(int32 X=-1;X<=1;++X) for(int32 Y=-1;Y<=1;++Y) for(int32 Z=-1;Z<=1;++Z)
                if(const auto* Candidates=Positions.Find(G+FIntVector(X,Y,Z)))
                    for(const auto& Candidate:*Candidates) if((Candidate.Value-Pos).SizeSquared()<Cell*Cell)
                    { FMorphTargetDelta V; V.SourceIdx=Candidate.Key; V.PositionDelta=Delta; V.TangentZDelta=FVector3f::ZeroVector; Unique.Add(V.SourceIdx,V); Found=true; }
            if(!Found) return FString::Printf(TEXT("ERROR unmatched source vertex %s %s"),*Pair.Key,*Pos.ToString());
        }
        auto& Deltas=Prepared.Add(Name); Unique.GenerateValueArray(Deltas);
        Deltas.Sort([](const auto& A,const auto& B){return A.SourceIdx<B.SourceIdx;}); Count+=Deltas.Num();
    }
    // Validate every source position before mutating the shared mesh.
    Mesh->Modify(); Mesh->ModifyMeshDescription(0);
    for(auto& Pair:Prepared)
    {
        const FName Name(*Pair.Key);
        if(!Attributes.GetMorphTargetNames().Contains(Name)) Attributes.RegisterMorphTargetAttribute(Name,false);
        auto Deltas=Attributes.GetVertexMorphPositionDelta(Name);
        for(const FVertexID Vertex:Description->Vertices().GetElementIDs()) Deltas[Vertex]=FVector3f::ZeroVector;
        for(const auto& Delta:Pair.Value) Deltas[FVertexID(Delta.SourceIdx)]=Delta.PositionDelta;
    }
    Mesh->CommitMeshDescription(0); Mesh->PostEditChange();
    FSkinnedAssetCompilingManager::Get().FinishCompilation({Mesh}); Mesh->MarkPackageDirty();
    return FString::Printf(TEXT("OK morphs=%d deltas=%d"),Prepared.Num(),Count);
}
