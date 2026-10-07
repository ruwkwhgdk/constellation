#include "CombatSurfaceContact.h"
#include "Components/SkeletalMeshComponent.h"
#include "Rendering/SkeletalMeshRenderData.h"
#include "Rendering/SkeletalMeshLODRenderData.h"
#include "Rendering/SkinWeightVertexBuffer.h"

bool CombatSurfaceContact::ConsiderTriangle(const FVector& Contact,const FVector& A,const FVector& B,const FVector& C,
    double& BestDistanceSquared,FVector& OutPosition)
{
    if (A.ContainsNaN() || B.ContainsNaN() || C.ContainsNaN() ||
        FVector::CrossProduct(B-A,C-A).IsNearlyZero()) return false;
    const FVector Point=FMath::ClosestPointOnTriangleToPoint(Contact,A,B,C);
    const double Distance=FVector::DistSquared(Contact,Point);
    if (!FMath::IsFinite(Distance) || Distance>=BestDistanceSquared) return false;
    BestDistanceSquared=Distance;OutPosition=Point;return true;
}

bool CombatSurfaceContact::Resolve(USkeletalMeshComponent* Mesh,const FVector& Contact,const FVector& Normal,
    FVector& OutPosition,FVector& OutNormal,int32& OutTriangles)
{
    OutTriangles=0;
    if (!Mesh || Contact.ContainsNaN() || !Mesh->GetSkeletalMeshAsset()) return false;
    const FSkeletalMeshRenderData* Data=Mesh->GetSkeletalMeshRenderData();
    const int32 LODIndex=Mesh->GetPredictedLODLevel();
    if (!Data || !Data->LODRenderData.IsValidIndex(LODIndex)) return false;
    const FSkeletalMeshLODRenderData& LOD=Data->LODRenderData[LODIndex];
    const auto& Positions=LOD.StaticVertexBuffers.PositionVertexBuffer;
    const auto* Indices=LOD.MultiSizeIndexContainer.GetIndexBuffer();
    auto* Weights=Mesh->GetSkinWeightBuffer(LODIndex);
    // CPU buffers can be stripped in cooked content. Never trigger a render flush or GPU readback.
    // The current slime uses fixed influences; unsupported future layouts retain the combat contact.
    if (!Positions.GetVertexData() || !Indices || Indices->GetResourceDataSize()<=0 || !Weights ||
        !Weights->GetDataVertexBuffer()->GetWeightData() || Weights->GetVariableBonesPerVertex() ||
        Weights->GetNumVertices()<Positions.GetNumVertices() || LOD.RenderSections.IsEmpty()) return false;
    const int32 TriangleCount=Indices->Num()/3;
    if (!TriangleCount) return false;
    TArray<FMatrix44f> RefToLocal;
    Mesh->GetCurrentRefToLocalMatrices(RefToLocal,LODIndex);
    if (RefToLocal.IsEmpty()) return false;
    // Bone-skinned triangles, not ref-pose bounds. At most 3072 vertices per accepted hit,
    // independent of mesh size; no per-frame cache upkeep. Morph targets/material WPO are not included.
    constexpr int32 MaxTriangles=1024;
    const int32 Samples=FMath::Min(TriangleCount,MaxTriangles);
    double BestDistance=DBL_MAX;
    FVector BestPosition=Contact,BestNormal=Normal.GetSafeNormal(UE_SMALL_NUMBER,FVector::UpVector);
    const FTransform Transform=Mesh->GetComponentTransform();
    for (int32 Sample=0;Sample<Samples;++Sample)
    {
        const int32 Triangle=int32(int64(Sample)*TriangleCount/Samples);
        const uint32 IA=Indices->Get(Triangle*3),IB=Indices->Get(Triangle*3+1),IC=Indices->Get(Triangle*3+2);
        if (IA>=Positions.GetNumVertices() || IB>=Positions.GetNumVertices() || IC>=Positions.GetNumVertices()) continue;
        const FVector A=Transform.TransformPosition(FVector(USkinnedMeshComponent::GetSkinnedVertexPosition(Mesh,IA,LOD,*Weights,RefToLocal)));
        const FVector B=Transform.TransformPosition(FVector(USkinnedMeshComponent::GetSkinnedVertexPosition(Mesh,IB,LOD,*Weights,RefToLocal)));
        const FVector C=Transform.TransformPosition(FVector(USkinnedMeshComponent::GetSkinnedVertexPosition(Mesh,IC,LOD,*Weights,RefToLocal)));
        ++OutTriangles;
        if (ConsiderTriangle(Contact,A,B,C,BestDistance,BestPosition))
        {
            BestNormal=FVector::CrossProduct(B-A,C-A).GetSafeNormal();
            if (FVector::DotProduct(BestNormal,Normal)<0) BestNormal=-BestNormal;
        }
    }
    if (BestDistance==DBL_MAX) return false;
    OutPosition=BestPosition;OutNormal=BestNormal;return true;
}
