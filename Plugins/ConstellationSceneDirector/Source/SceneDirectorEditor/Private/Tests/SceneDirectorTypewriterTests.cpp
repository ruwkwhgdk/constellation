#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "DirectorDialogueReveal.h"
#include "SDirectorDialogue.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorTypewriterTest,"Constellation.SceneDirector.DialogueTypewriter",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorTypewriterTest::RunTest(const FString&)
{
    FDirectorDialogueReveal Reveal;
    const FText Source=FText::FromString(TEXT("가 <teal>나&amp;다</>!"));
    Reveal.Reset(Source,.1f);
    TestTrue(TEXT("Starts unrevealed"),Reveal.GetText().IsEmpty());
    Reveal.Advance(.1f);
    TestEqual(TEXT("One visible character per interval; whitespace costs no interval"),Reveal.GetText().ToString(),FString(TEXT("가 ")));
    Reveal.Advance(.1f);
    TestEqual(TEXT("Partial rich text keeps complete balanced tags"),Reveal.GetText().ToString(),FString(TEXT("가 <teal>나</>")));
    Reveal.Advance(.1f);
    TestEqual(TEXT("Entity is one visible character"),Reveal.GetText().ToString(),FString(TEXT("가 <teal>나&amp;</>")));
    TestTrue(TEXT("Reveal consumes first advance"),Reveal.Finish());
    TestFalse(TEXT("Completed reveal does not consume next advance"),Reveal.Finish());
    TestTrue(TEXT("Completion retains localized source FText"),Reveal.GetText().IdenticalTo(Source));
    Reveal.Reset(FText::FromString(TEXT("e\u0301!")),.1f);
    Reveal.Advance(.1f);
    TestEqual(TEXT("Combining character reveals with its base"),Reveal.GetText().ToString(),FString(TEXT("e\u0301")));
    Reveal.Reset(Source,0.f);
    TestTrue(TEXT("Disabled effect shows original text immediately"),Reveal.GetText().IdenticalTo(Source));
    Reveal.Reset(FText::FromString(TEXT("ABCD")),.1f,.2f);
    Reveal.Advance(.1f);
    TestEqual(TEXT("Timed lines speed up to fit their existing cue"),Reveal.GetText().ToString(),FString(TEXT("AB")));
    Reveal.Advance(.1f);
    TestFalse(TEXT("Timed reveal finishes without extending the song cue"),Reveal.IsRevealing());
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDirectorTypewriterLayoutTest,"Constellation.SceneDirector.DialogueTypewriterLayout",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FDirectorTypewriterLayoutTest::RunTest(const FString&)
{
    const FText LongLine=FText::FromString(TEXT("First line\nSecond line\nThird line\nFourth line\nFifth line\nSixth line"));
    FGuid Prompt=FGuid::NewGuid();
    auto Widget=SNew(SDirectorDialogue).Background(nullptr).Continue(nullptr).SpeakerBackground(nullptr)
        .Dialogue(LongLine).CharacterInterval(.1f).Waiting(true).ChoicePrompt_Lambda([&Prompt]{return Prompt;});
    Widget->SlatePrepass();
    const FVector2D TypingSize=Widget->GetDesiredSize();
    TestTrue(TEXT("First advance reveals the line"),Widget->FinishReveal());
    Widget->SlatePrepass();
    TestEqual(TEXT("Multiline dialogue has its final size before the first glyph"),FVector2D(Widget->GetDesiredSize()),TypingSize);
    TestFalse(TEXT("Next advance is available for dialogue progression"),Widget->FinishReveal());
    Prompt.Invalidate();Widget->SlatePrepass();
    TestFalse(TEXT("A retained line does not retype when its timed cue ends"),Widget->FinishReveal());
    Prompt=FGuid::NewGuid();Widget->SlatePrepass();
    TestTrue(TEXT("A new cue with identical text still types again"),Widget->FinishReveal());
    return true;
}
#endif
