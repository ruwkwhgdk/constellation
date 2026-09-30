#include "ResourceRecoveryLibrary.h"
#include "Animation/AnimationAsset.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimData/IAnimationDataController.h"
#include "Animation/Skeleton.h"
#include "Modules/ModuleManager.h"

IMPLEMENT_MODULE(FDefaultModuleImpl, ConstellationResourceTools)

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
