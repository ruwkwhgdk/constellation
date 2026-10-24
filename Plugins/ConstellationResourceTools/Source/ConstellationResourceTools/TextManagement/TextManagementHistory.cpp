#include "TextManagementHistory.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/Paths.h"
#include "Misc/Base64.h"
#include "HAL/FileManager.h"

namespace ConstellationText
{
static FString RevisionFile(const FString& Directory,const FString& Id){return Directory/(Id+TEXT(".ini"));}
static bool WriteRevision(const FString& Directory,const FTextRevision& R)
{
    if(!IFileManager::Get().MakeDirectory(*Directory,true))return false;
    FConfigFile File;
    File.SetString(TEXT("Revision"),TEXT("Id"),*R.Id);File.SetString(TEXT("Revision"),TEXT("Target"),*R.TargetId);
    File.SetString(TEXT("Revision"),TEXT("Time"),*R.Time);File.SetString(TEXT("Revision"),TEXT("Before"),*FBase64::Encode(R.Before));
    File.SetString(TEXT("Revision"),TEXT("After"),*FBase64::Encode(R.After));File.SetString(TEXT("Revision"),TEXT("State"),*R.State);
    File.SetString(TEXT("Revision"),TEXT("RestoredFrom"),*R.RestoredFrom);
    const FString Target=RevisionFile(Directory,R.Id),Temp=Target+TEXT(".tmp");
    if(!File.Write(Temp))return false;
    return IFileManager::Get().Move(*Target,*Temp,true,true,false,true);
}
static bool ReadRevision(const FString& Filepath,FTextRevision& R)
{
    FConfigFile File;File.Read(Filepath);
    if(!File.GetString(TEXT("Revision"),TEXT("Id"),R.Id)||!File.GetString(TEXT("Revision"),TEXT("Target"),R.TargetId)||!File.GetString(TEXT("Revision"),TEXT("Before"),R.Before)||!File.GetString(TEXT("Revision"),TEXT("After"),R.After))return false;
    FString Before,After;
    if(!FBase64::Decode(R.Before,Before)||!FBase64::Decode(R.After,After))return false;
    R.Before=MoveTemp(Before);R.After=MoveTemp(After);
    File.GetString(TEXT("Revision"),TEXT("Time"),R.Time);File.GetString(TEXT("Revision"),TEXT("State"),R.State);File.GetString(TEXT("Revision"),TEXT("RestoredFrom"),R.RestoredFrom);return true;
}
TArray<FTextRevision> ReadTextHistory(const FString& Directory,const FString& TargetId)
{
    TArray<FTextRevision> Result;TArray<FString> Files;IFileManager::Get().FindFiles(Files,*(Directory/TEXT("*.ini")),true,false);
    for(const FString& File:Files){FTextRevision R;if(ReadRevision(Directory/File,R)&&R.TargetId==TargetId)Result.Add(MoveTemp(R));}
    Result.Sort([](const FTextRevision& A,const FTextRevision& B){return A.Time>B.Time;});return Result;
}
static bool CurrentMatches(const FTextDraft& Draft,FText& Message)
{
    FEntry Entry;Entry.Origin=Entry.Location=Draft.Base.Target;FEditSnapshot Current;
    if(!ReadEdit(Entry,Current,Message))return false;
    if(Current.Source!=Draft.Base.Source||(Current.Target.Kind!=ELocationKind::StringTable&&!Current.Original.IdenticalTo(Draft.Base.Original)))
    {Message=FText::FromString(TEXT("외부에서 원문이 변경됐습니다. 초안을 유지했습니다. 최신 원문과 비교한 뒤 다시 편집하세요."));return false;}
    return true;
}
bool CommitTextDraft(FTextDraft& Draft,const FString& Directory,FText& Message,TFunctionRef<bool(const FLocation&,FText&)> Saver)
{
    if(!CurrentMatches(Draft,Message))return false;
    if(!Draft.IsDirty()){Message=FText::FromString(TEXT("변경된 내용이 없습니다."));return true;}
    FTextRevision Revision;
    if(!Draft.PendingId.IsEmpty())
    {
        if(!ReadRevision(RevisionFile(Directory,Draft.PendingId),Revision)||Revision.TargetId!=Draft.Base.Target.Id())
        {Message=FText::FromString(TEXT("저장 대기 이력을 읽지 못했습니다. 초안은 유지됩니다."));return false;}
    }
    else
    {
        Revision.Id=FGuid::NewGuid().ToString(EGuidFormats::Digits);Revision.TargetId=Draft.Base.Target.Id();Revision.Before=Draft.Base.Source;
        Revision.Time=FDateTime::UtcNow().ToIso8601();Revision.RestoredFrom=Draft.RestoredFrom;
    }
    Revision.After=Draft.Text;Revision.State=TEXT("Pending");
    // Journal first: a crash or failed asset save must never appear as a successful revision.
    if(!WriteRevision(Directory,Revision)){Message=FText::FromString(TEXT("변경 이력을 기록하지 못해 저장을 시작하지 않았습니다. 초안은 유지됩니다."));return false;}
    Draft.PendingId=Revision.Id;
    if(!ApplyEdit(Draft.Base,Draft.Text,Message)){Revision.State=TEXT("Failed");WriteRevision(Directory,Revision);return false;}
    FEntry Entry;Entry.Location=Entry.Origin=Draft.Base.Target;FEditSnapshot Applied;
    if(!ReadEdit(Entry,Applied,Message)){Message=FText::FromString(TEXT("적용 후 원문을 읽지 못했습니다. 디스크 저장은 수행하지 않았습니다."));return false;}
    Draft.Base=Applied;
    if(!Saver(Draft.Base.Target,Message))
    {Revision.State=TEXT("Failed");WriteRevision(Directory,Revision);Message=FText::FromString(TEXT("원본에는 적용됐지만 디스크 저장이 실패했거나 취소됐습니다. 초안을 유지했으며 저장 버튼으로 재시도할 수 있습니다."));return false;}
    Revision.State=TEXT("Saved");Revision.Time=FDateTime::UtcNow().ToIso8601();const bool bRecorded=WriteRevision(Directory,Revision);
    Draft.PendingId.Reset();Draft.RestoredFrom.Reset();
    Message=FText::FromString(bRecorded?TEXT("저장됨 · 변경 이력에 기록했습니다."):TEXT("원본은 저장됐지만 이력 완료 기록에 실패했습니다. 이력의 저장 상태는 미확인으로 남습니다."));return true;
}
bool StageTextRestore(FTextDraft& Draft,const FTextRevision& Revision,FText& Message,bool bBefore)
{
    if(Revision.State!=TEXT("Saved")||Revision.TargetId!=Draft.Base.Target.Id())
    {Message=FText::FromString(TEXT("이 원문의 저장 완료 이력만 복원할 수 있습니다."));return false;}
    if(Draft.IsDirty()){Message=FText::FromString(TEXT("현재 초안을 먼저 저장하거나 비운 뒤 복원하세요."));return false;}
    if(!CurrentMatches(Draft,Message))return false;
    Draft.Text=bBefore?Revision.Before:Revision.After;Draft.RestoredFrom=Revision.Id;return true;
}
}
