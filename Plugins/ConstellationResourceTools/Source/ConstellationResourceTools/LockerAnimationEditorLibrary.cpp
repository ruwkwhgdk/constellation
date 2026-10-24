#include "LockerAnimationEditorLibrary.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimSequence.h"

bool ULockerAnimationEditorLibrary::ConfigureLockerMontage(UAnimMontage* Montage, UAnimSequence* Fall, UAnimSequence* Hold, UAnimSequence* GetUp)
{
    if (!Montage || !Fall || !Hold || !GetUp ||
        Montage->GetPathName() != TEXT("/Game/Constellation/Characters/Heroine/GamePilot/Locker/AM_Locker_Event.AM_Locker_Event")) return false;
    for (UAnimSequence* Sequence : {Fall, Hold, GetUp})
        if (Sequence->GetSkeleton() != Montage->GetSkeleton() || Sequence->GetPlayLength() <= 0.f) return false;

    Montage->Modify();
    Montage->SlotAnimTracks.Reset();
    FSlotAnimationTrack Track;
    Track.SlotName = TEXT("DefaultSlot");
    float Time = 0.f;
    for (UAnimSequence* Sequence : {Fall, Hold, GetUp})
    {
        FAnimSegment Segment;
        Segment.SetAnimReference(Sequence);
        Segment.StartPos = Time;
        Segment.AnimStartTime = 0.f;
        Segment.AnimEndTime = Sequence->GetPlayLength();
        Segment.AnimPlayRate = 1.f;
        Segment.LoopingCount = 1;
        Track.AnimTrack.AnimSegments.Add(Segment);
        Time += Sequence->GetPlayLength();
    }
    Montage->SlotAnimTracks.Add(Track);
    Montage->SetCompositeLength(Time);
    while (Montage->GetNumSections() > 0) Montage->DeleteAnimCompositeSection(Montage->GetNumSections() - 1);
    Montage->AddAnimCompositeSection(TEXT("ExitFall"), 0.f);
    Montage->AddAnimCompositeSection(TEXT("ProneHold"), Fall->GetPlayLength());
    Montage->AddAnimCompositeSection(TEXT("GetUp"), Fall->GetPlayLength() + Hold->GetPlayLength());
    Montage->GetAnimCompositeSection(0).NextSectionName = TEXT("ProneHold");
    Montage->GetAnimCompositeSection(1).NextSectionName = TEXT("ProneHold");
    Montage->GetAnimCompositeSection(2).NextSectionName = NAME_None;
    Montage->bEnableAutoBlendOut = false;
    Montage->BlendIn.SetBlendTime(0.f);
    Montage->BlendOut.SetBlendTime(0.f);
    Montage->MarkPackageDirty();
    Montage->PostEditChange();
    return true;
}
