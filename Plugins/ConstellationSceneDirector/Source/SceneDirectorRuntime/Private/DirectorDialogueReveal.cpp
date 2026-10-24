#include "DirectorDialogueReveal.h"
#include "Internationalization/BreakIterator.h"

void FDirectorDialogueReveal::Reset(const FText& Text,float SecondsPerCharacter,float MaxDuration)
{
    Source=Text;Markup=Text.ToString();Ends.Reset();Depths.Reset();Visible=0;Elapsed=0;
    const auto Breaks=FBreakIterator::CreateCharacterBoundaryIterator();Breaks->SetString(Markup);
    int32 Depth=0;
    for(int32 Index=0;Index<Markup.Len();)
    {
        if(Markup[Index]==TEXT('<'))
        {
            const int32 End=Markup.Find(TEXT(">"),ESearchCase::CaseSensitive,ESearchDir::FromStart,Index);
            if(End!=INDEX_NONE)
            {
                if(Markup.Mid(Index,2)==TEXT("</"))Depth=FMath::Max(0,Depth-1);
                else if(End>Index&&Markup[End-1]!=TEXT('/'))++Depth;
                Index=End+1;continue;
            }
        }
        int32 End=Breaks->MoveToCandidateAfter(Index);
        if(End==INDEX_NONE||End<=Index)End=Index+1;
        if(Markup[Index]==TEXT('&'))
        {
            for(const TCHAR* Entity:{TEXT("&amp;"),TEXT("&lt;"),TEXT("&gt;"),TEXT("&quot;")})
                if(Markup.Mid(Index,FCString::Strlen(Entity))==Entity){End=Index+FCString::Strlen(Entity);break;}
        }
        if(FChar::IsWhitespace(Markup[Index]))
        {
            if(!Ends.IsEmpty()){Ends.Last()=End;Depths.Last()=Depth;}
        }
        else {Ends.Add(End);Depths.Add(Depth);}
        Index=End;
    }
    Interval=FMath::Max(0.f,SecondsPerCharacter);
    if(MaxDuration>0.f&&!Ends.IsEmpty())Interval=FMath::Min(Interval,double(MaxDuration)/Ends.Num());
    if(Interval<=0)Visible=Ends.Num();
}
bool FDirectorDialogueReveal::Advance(float DeltaSeconds)
{
    if(!IsRevealing())return false;
    Elapsed+=FMath::Max(0.f,DeltaSeconds);
    const int32 Previous=Visible;
    Visible=FMath::Min(Ends.Num(),FMath::FloorToInt((Elapsed+1.e-6)/Interval));
    return Visible>Previous;
}
bool FDirectorDialogueReveal::Finish()
{
    const bool WasRevealing=IsRevealing();Visible=Ends.Num();return WasRevealing;
}
FText FDirectorDialogueReveal::GetText() const
{
    if(!IsRevealing())return Source;
    if(Visible==0)return FText::GetEmpty();
    FString Prefix=Markup.Left(Ends[Visible-1]);
    for(int32 I=0;I<Depths[Visible-1];++I)Prefix+=TEXT("</>");
    return FText::FromString(MoveTemp(Prefix));
}
