#include "CombatWorkbenchSubsystem.h"
#include "CombatLabCharacter.h"
#include "CombatAbilitySystem.h"
#include "CombatActionDefinition.h"
#include "Animation/AnimMontage.h"
#include "CombatPatternProfile.h"
#include "CombatEncounterProfile.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "UObject/UnrealType.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"

namespace
{
void* FieldData(const FCombatTuningField& F,FProperty*& P)
{
    UObject* O=F.Object.Get();
    if(!O) return nullptr;
    if(F.PatternIndex!=INDEX_NONE)
    {
        auto* Profile=Cast<UCombatPatternProfile>(O);
        if(!Profile || !Profile->Patterns.IsValidIndex(F.PatternIndex)) return nullptr;
        P=FCombatPatternEntry::StaticStruct()->FindPropertyByName(F.Property);
        return P?P->ContainerPtrToValuePtr<void>(&Profile->Patterns[F.PatternIndex]):nullptr;
    }
    P=O->GetClass()->FindPropertyByName(F.Property);
    return P?P->ContainerPtrToValuePtr<void>(O):nullptr;
}
bool SafeName(const FString& Name)
{
    if(Name.IsEmpty() || Name.Len()>64) return false;
    for(TCHAR C:Name) if(!((C>='a'&&C<='z')||(C>='A'&&C<='Z')||(C>='0'&&C<='9')||C=='_'||C=='-')) return false;
    return true;
}
FString PresetDir(){return FPaths::ProjectSavedDir()/TEXT("CombatTuning");}
}

double UCombatWorkbenchSubsystem::ReadField(const FCombatTuningField& F) const
{
    FProperty* P=nullptr; void* Data=FieldData(F,P);
    if(!Data) return 0;
    if(auto* B=CastField<FBoolProperty>(P)) return B->GetPropertyValue(Data)?1:0;
    if(auto* N=CastField<FNumericProperty>(P))
        return N->IsInteger()?double(N->GetSignedIntPropertyValue(Data)):N->GetFloatingPointPropertyValue(Data);
    return 0;
}
void UCombatWorkbenchSubsystem::WriteField(const FCombatTuningField& F,double V)
{
    FProperty* P=nullptr; void* Data=FieldData(F,P); if(!Data) return;
    if(auto* B=CastField<FBoolProperty>(P)) B->SetPropertyValue(Data,V!=0);
    else if(auto* N=CastField<FNumericProperty>(P))
    { if(N->IsInteger()) N->SetIntPropertyValue(Data,int64(V)); else N->SetFloatingPointPropertyValue(Data,V); }
}
void UCombatWorkbenchSubsystem::Add(UObject* O,const TCHAR* Prop,const FString& Key,const FString& Label,
    const FString& Group,const FString& ActorKey,bool Enemy,double Min,double Max,bool Pattern,int32 Index)
{
    FCombatTuningField F;
    F.Object=O; F.Property=Prop; F.Key=ActorKey+TEXT("/")+Key; F.ActorKey=ActorKey;
    F.Label=Label; F.Group=Group; F.bEnemy=Enemy; F.bPattern=Pattern; F.Min=Min; F.Max=Max; F.PatternIndex=Index;
    FProperty* P=nullptr;
    if(!FieldData(F,P)) return;
    F.bBoolean=CastField<FBoolProperty>(P)!=nullptr;
    if(auto* N=CastField<FNumericProperty>(P)) F.bInteger=N->IsInteger();
    F.DefaultValue=F.Value=ReadField(F);
    if(AppliedSources.FindRef(ActorKey)==Sources.FindRef(ActorKey))
        if(const double* V=Applied.Find(F.Key)) { WriteField(F,*V); F.Value=*V; }
    Fields.Add(F);
}

void UCombatWorkbenchSubsystem::PrepareActor(ACombatLabCharacter* A)
{
    if(!A) return;
    if(FieldWorld.Get()!=A->GetWorld())
    { Fields.Reset(); Actors.Reset(); Copies.Reset(); Sources.Reset(); FieldWorld=A->GetWorld(); }
    if(Actors.Contains(A)) return;
    Actors.Add(A);
    const FString ActorKey=A->GetWorld()->GetOutermost()->GetName()+TEXT("/")+A->GetName();
    const bool Enemy=A->bTrainingEnemy;
    FString Signature=GetPathNameSafe(A->GetMesh()->GetSkeletalMeshAsset())+TEXT("|")+GetPathNameSafe(A->Action)+TEXT("|")+GetPathNameSafe(A->PatternProfile)+TEXT("|")+GetPathNameSafe(A->EncounterProfile);
    if(A->SkillAction) Signature+=TEXT("|skill:")+GetPathNameSafe(A->SkillAction);
    if(A->UltimateAction) Signature+=TEXT("|ultimate:")+GetPathNameSafe(A->UltimateAction);
    if(A->PatternProfile) for(const auto& Entry:A->PatternProfile->Patterns)
        Signature+=TEXT("|pattern:")+Entry.Id.ToString()+TEXT("=")+GetPathNameSafe(Entry.Action);
    TMap<UCombatActionDefinition*,UCombatActionDefinition*> Clones;
    TArray<TPair<FString,UCombatActionDefinition*>> Actions;
    TFunction<UCombatActionDefinition*(UCombatActionDefinition*)> Clone=[&](UCombatActionDefinition* Source)->UCombatActionDefinition*
    {
        if(!Source) return nullptr;
        if(auto** Existing=Clones.Find(Source)) return *Existing;
        auto* Copy=DuplicateObject<UCombatActionDefinition>(Source,this,MakeUniqueObjectName(this,Source->GetClass(),Source->GetFName()));
        Copy->SetFlags(RF_Transient); Copies.Add(Copy); Clones.Add(Source,Copy);
        Actions.Emplace(Source->GetPathName(),Copy);
        Copy->NextAction=Clone(Source->NextAction);
        return Copy;
    };
    A->Action=Clone(A->Action);
    A->SkillAction=Clone(A->SkillAction);
    A->UltimateAction=Clone(A->UltimateAction);
    if(A->PatternProfile)
    {
        A->PatternProfile=DuplicateObject<UCombatPatternProfile>(A->PatternProfile,this,MakeUniqueObjectName(this,A->PatternProfile->GetClass(),A->PatternProfile->GetFName()));
        A->PatternProfile->SetFlags(RF_Transient); Copies.Add(A->PatternProfile);
        for(auto& Entry:A->PatternProfile->Patterns) Entry.Action=Clone(Entry.Action);
    }
    if(A->EncounterProfile)
    {
        A->EncounterProfile=DuplicateObject<UCombatEncounterProfile>(A->EncounterProfile,this,MakeUniqueObjectName(this,A->EncounterProfile->GetClass(),A->EncounterProfile->GetFName()));
        A->EncounterProfile->SetFlags(RF_Transient); Copies.Add(A->EncounterProfile);
    }
    for(const auto& Pair:Actions) Signature+=TEXT("|")+Pair.Key;
    Sources.Add(ActorKey,Signature);
    auto C=[&](const TCHAR* Prop,const TCHAR* Label,const TCHAR* Group,double Min=0,double Max=100000)
    {Add(A->Combat,Prop,FString(TEXT("Combat/"))+Prop,Label,Group,ActorKey,Enemy,Min,Max);};
    C(TEXT("MaxHealth"),TEXT("최대 HP"),TEXT("자원"),1);
    C(TEXT("MaxStamina"),TEXT("최대 SP"),TEXT("자원"),1);
    C(TEXT("StaminaRecoveryPerSecond"),TEXT("SP 회복량 / 초"),TEXT("자원"));
    C(TEXT("StaminaRecoveryDelay"),TEXT("SP 회복 대기 (s)"),TEXT("자원"),0,120);
    C(TEXT("HitReactionDuration"),TEXT("피격 경직 (s)"),TEXT("피격"),0,30);
    if(!Enemy)
    {
        Add(A->GetCharacterMovement(),TEXT("MaxWalkSpeed"),TEXT("Movement/MaxWalkSpeed"),TEXT("이동 속도 (cm/s)"),TEXT("이동"),ActorKey,false,1,3000);
        C(TEXT("DodgeDuration"),TEXT("지속 시간 (s)"),TEXT("회피"),.01,10);
        C(TEXT("DodgeDistance"),TEXT("거리 (cm)"),TEXT("회피"),.01,3000);
        C(TEXT("DodgeStaminaCost"),TEXT("SP 비용"),TEXT("회피"));
        C(TEXT("DodgeInvulnerableStart"),TEXT("무적 시작 (s)"),TEXT("회피"),0,10);
        C(TEXT("DodgeInvulnerableEnd"),TEXT("무적 종료 (s)"),TEXT("회피"),0,10);
    }
    if(auto* E=A->EncounterProfile.Get())
    {
        auto P=[&](const TCHAR* Prop,const TCHAR* Label,double Min=1,double Max=100000)
        {Add(E,Prop,FString(TEXT("Encounter/"))+Prop,Label,TEXT("이동 · 교전 · 복귀"),ActorKey,Enemy,Min,Max);};
        P(TEXT("MoveSpeed"),TEXT("이동 속도 (cm/s)"),1,3000);
        P(TEXT("DetectRadius"),TEXT("감지 거리 (cm)"));
        P(TEXT("LoseRadius"),TEXT("추적 해제 거리 (cm)"));
        P(TEXT("LeashRadius"),TEXT("활동 반경 (cm)"));
        P(TEXT("AttackDistance"),TEXT("공격 접근 거리 (cm)"));
        P(TEXT("LostSightTime"),TEXT("시야 상실 유예 (s)"),0,120);
        P(TEXT("HomeTolerance"),TEXT("복귀 완료 거리 (cm)"));
        P(TEXT("bRestoreOnReturn"),TEXT("복귀 시 HP / SP 회복"),0,1);
    }
    int32 ActionNumber=0;
    for(const auto& Pair:Actions)
    {
        ++ActionNumber;
        const FString Group=FString::Printf(TEXT("공격 %d · %s"),ActionNumber,*Pair.Value->DisplayName.ToString());
        auto P=[&](const TCHAR* Prop,const TCHAR* Label,double Min=0,double Max=100000)
        {Add(Pair.Value,Prop,TEXT("Action/")+Pair.Key+TEXT("/")+Prop,Label,Group,ActorKey,Enemy,Min,Max,true);};
        P(TEXT("Damage"),TEXT("피해량")); P(TEXT("StaminaCost"),TEXT("SP 비용"));
        P(TEXT("bRadialHit"),TEXT("구형 범위 판정"),0,1);
        P(TEXT("DashDistance"),TEXT("돌진 거리 (cm)"),0,3000); P(TEXT("DashDuration"),TEXT("돌진 시간 (s)"),.01,10);
        P(TEXT("UltimateCost"),TEXT("궁극기 게이지 비용"),0,100); P(TEXT("UltimateGain"),TEXT("적중 시 게이지 획득"),0,100);
        P(TEXT("Cooldown"),TEXT("쿨다운 (s)"),0,120); P(TEXT("PlayRate"),TEXT("재생 배속"),.1,5);
        P(TEXT("Reach"),TEXT("판정 거리 (cm)"),1,3000); P(TEXT("Radius"),TEXT("판정 반경 (cm)"),1,1000);
        P(TEXT("bAllowDodgeCancel"),TEXT("공격 중 회피 전환 허용"),0,1);
        P(TEXT("DodgeCancelStart"),TEXT("회피 전환 시작 (몽타주 s)"),0,120);
        P(TEXT("DodgeCancelEnd"),TEXT("회피 전환 종료 (몽타주 s)"),0,120);
        if(Pair.Value->NextAction)
        {
            const double Length=Pair.Value->Montage?Pair.Value->Montage->GetPlayLength():0;
            P(TEXT("InputWindowStart"),TEXT("선입력 시작 (몽타주 s)"),0,Length);
            P(TEXT("InputWindowEnd"),TEXT("선입력 종료 (몽타주 s)"),0,Length);
        }
    }
    if(auto* Profile=A->PatternProfile.Get()) for(int32 I=0;I<Profile->Patterns.Num();++I)
    {
        const FString Group=TEXT("패턴 · ")+Profile->Patterns[I].Id.ToString();
        auto P=[&](const TCHAR* Prop,const TCHAR* Label,double Min=0,double Max=100000)
        {Add(Profile,Prop,FString::Printf(TEXT("Pattern/%d/%s"),I,Prop),Label,Group,ActorKey,Enemy,Min,Max,true,I);};
        P(TEXT("MinDistance"),TEXT("최소 거리 (cm)")); P(TEXT("MaxDistance"),TEXT("최대 거리 (cm)"));
        P(TEXT("MaxAngle"),TEXT("최대 각도 (°)"),0,180);
        P(TEXT("Weight"),TEXT("선택 가중치"),0,1000); P(TEXT("MaxConsecutive"),TEXT("연속 제한 (0 = 무제한)"),0,100);
        P(TEXT("bRequireSight"),TEXT("시야 필요"),0,1);
    }
}
TArray<double> UCombatWorkbenchSubsystem::ReadValues() const
{
    TArray<double> V; for(const auto& F:Fields) V.Add(ReadField(F)); return V;
}
bool UCombatWorkbenchSubsystem::ValidateValues(const TArray<double>& V,FString& Error)
{
    if(V.Num()!=Fields.Num() || V.IsEmpty()) {Error=TEXT("현재 시험장의 설정 항목과 일치하지 않습니다."); return false;}
    for(int32 I=0;I<V.Num();++I)
    {
        const auto& F=Fields[I];
        if(!F.Object.IsValid() || !FMath::IsFinite(V[I]) || V[I]<F.Min || V[I]>F.Max ||
            ((F.bBoolean||F.bInteger) && V[I]!=FMath::FloorToDouble(V[I])))
        {Error=F.Group+TEXT(" / ")+F.Label+TEXT(": 허용 범위를 확인하세요."); return false;}
    }
    const TArray<double> Old=ReadValues();
    for(int32 I=0;I<V.Num();++I) WriteField(Fields[I],V[I]);
    bool Valid=true;
    for(auto Weak:Actors) if(auto* A=Weak.Get())
    {
        auto* C=A->Combat.Get();
        if(C->DodgeInvulnerableStart>=C->DodgeInvulnerableEnd || C->DodgeInvulnerableEnd>C->DodgeDuration)
        {Error=TEXT("회피: 무적 시작 < 종료 ≤ 지속 시간이어야 합니다."); Valid=false; break;}
        if(A->EncounterProfile && !A->EncounterProfile->Validate(Error)) {Valid=false; break;}
        if(A->PatternProfile && !A->PatternProfile->Validate(Error)) {Valid=false; break;}
    }
    if(Valid) for(auto O:Copies)
        if(auto* Action=Cast<UCombatActionDefinition>(O))
        {
            if(Action->NextAction && Action->InputWindowStart>=Action->InputWindowEnd)
            {Error=Action->DisplayName.ToString()+TEXT(": 선입력 시작 < 종료여야 합니다.");Valid=false;break;}
            if(!Action->Validate(Error)) {Valid=false; break;}
        }
    for(int32 I=0;I<Old.Num();++I) WriteField(Fields[I],Old[I]);
    if(Valid) Error.Reset();
    return Valid;
}
bool UCombatWorkbenchSubsystem::ApplyValues(const TArray<double>& V,FString& Error)
{
    if(!ValidateValues(V,Error)) return false;
    for(int32 I=0;I<V.Num();++I) Applied.Add(Fields[I].Key,V[I]);
    for(const auto& Pair:Sources) AppliedSources.Add(Pair.Key,Pair.Value);
    return true;
}
TSharedRef<FJsonObject> UCombatWorkbenchSubsystem::MakePresetDocument(const TArray<double>& V) const
{
    auto Root=MakeShared<FJsonObject>(); Root->SetNumberField(TEXT("schema_version"),4);
    Root->SetStringField(TEXT("kind"),TEXT("ConstellationCombatTuning"));
    auto JsonSources=MakeShared<FJsonObject>();
    for(const auto& Pair:Sources) JsonSources->SetStringField(Pair.Key,Pair.Value);
    Root->SetObjectField(TEXT("sources"),JsonSources);
    auto JsonValues=MakeShared<FJsonObject>();
    for(int32 I=0;I<V.Num();++I) JsonValues->SetNumberField(Fields[I].Key,V[I]);
    Root->SetObjectField(TEXT("values"),JsonValues);
    return Root;
}
bool UCombatWorkbenchSubsystem::SavePreset(const TArray<double>& V,const FString& Name,FString& Result)
{
    if(!SafeName(Name)) {Result=TEXT("이름: 영문·숫자·_·- 사용, 1~64자."); return false;}
    if(!ValidateValues(V,Result)) return false;
    const FString Path=PresetDir()/(Name+TEXT(".json"));
    if(IFileManager::Get().FileExists(*Path)) {Result=TEXT("같은 이름이 있습니다. 새 이름으로 저장하세요."); return false;}
    auto Root=MakePresetDocument(V);
    FString Text; FJsonSerializer::Serialize(Root,TJsonWriterFactory<>::Create(&Text));
    IFileManager::Get().MakeDirectory(*PresetDir(),true);
    if(!FFileHelper::SaveStringToFile(Text,*Path,FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM,&IFileManager::Get(),FILEWRITE_NoReplaceExisting))
    {Result=TEXT("프리셋 파일을 저장하지 못했습니다."); return false;}
    Result=TEXT("저장 완료: Saved/CombatTuning/")+Name+TEXT(".json"); return true;
}
bool UCombatWorkbenchSubsystem::LoadPreset(const FString& Name,TArray<double>& V,FString& Error)
{
    if(!SafeName(Name)) {Error=TEXT("올바른 프리셋 이름을 선택하세요."); return false;}
    FString Text; TSharedPtr<FJsonObject> Root;
    if(!FFileHelper::LoadFileToString(Text,*(PresetDir()/(Name+TEXT(".json")))) ||
        !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Root))
    {Error=TEXT("프리셋 파일을 읽지 못했습니다.");return false;}
    return ReadPresetDocument(Root,V,Error);
}
bool UCombatWorkbenchSubsystem::ReadPresetDocument(const TSharedPtr<FJsonObject>& Root,TArray<double>& V,FString& Error)
{
    double Version=0;FString Kind;
    const TSharedPtr<FJsonObject>* JS=nullptr;const TSharedPtr<FJsonObject>* JV=nullptr;
    if(!Root.IsValid() ||
        !Root->HasTypedField<EJson::Number>(TEXT("schema_version")) || !Root->TryGetNumberField(TEXT("schema_version"),Version) || (Version!=1 && Version!=2 && Version!=3 && Version!=4) ||
        !Root->TryGetStringField(TEXT("kind"),Kind) || Kind!=TEXT("ConstellationCombatTuning") ||
        !Root->TryGetObjectField(TEXT("sources"),JS) || !Root->TryGetObjectField(TEXT("values"),JV))
    {Error=TEXT("프리셋 형식 또는 버전이 올바르지 않습니다.");return false;}
    if((*JS)->Values.Num()!=Sources.Num())
    {Error=TEXT("다른 시험장 또는 다른 구성의 프리셋입니다."); return false;}
    for(const auto& Pair:Sources)
    {
        FString Source;
        if(!(*JS)->TryGetStringField(Pair.Key,Source) || Source!=Pair.Value)
        {Error=TEXT("원본 자산 또는 대상이 일치하지 않습니다."); return false;}
    }
    TSet<FString> KnownKeys;
    for(const auto& F:Fields) KnownKeys.Add(F.Key);
    for(const auto& Pair:(*JV)->Values)
    {
        const FString Key(*Pair.Key);
        if(!KnownKeys.Contains(Key)) {Error=TEXT("현재 구성에 없는 설정: ")+Key;return false;}
    }
    int32 AddedDefaults=0;
    TArray<double> Draft;
    for(const auto& F:Fields)
    {
        double Number;
        const bool AddedIn2=F.Property==TEXT("InputWindowStart") || F.Property==TEXT("InputWindowEnd");
        const bool AddedIn3=F.Property==TEXT("bAllowDodgeCancel") || F.Property==TEXT("DodgeCancelStart") || F.Property==TEXT("DodgeCancelEnd");
        const bool AddedIn4=F.Property==TEXT("UltimateCost") || F.Property==TEXT("UltimateGain") || F.Property==TEXT("bRadialHit") || F.Property==TEXT("DashDistance") || F.Property==TEXT("DashDuration");
        if(!(*JV)->HasField(F.Key) && ((Version==1 && AddedIn2) || (Version<3 && AddedIn3) || (Version<4 && AddedIn4)))
        {Draft.Add(F.DefaultValue);++AddedDefaults;continue;}
        if(!(*JV)->HasTypedField<EJson::Number>(F.Key) || !(*JV)->TryGetNumberField(F.Key,Number)) {Error=TEXT("누락되거나 숫자가 아닌 설정: ")+F.Label; return false;}
        Draft.Add(Number);
    }
    if(!ValidateValues(Draft,Error)) return false;
    V=MoveTemp(Draft);
    if(AddedDefaults) Error=FString::Printf(TEXT("이전 프리셋: 새 설정 %d개 항목을 자산 초기값으로 보완했습니다."),AddedDefaults);
    return true;
}
TArray<FString> UCombatWorkbenchSubsystem::ListPresets() const
{
    TArray<FString> Files; IFileManager::Get().FindFiles(Files,*(PresetDir()/TEXT("*.json")),true,false);
    for(FString& File:Files) File=FPaths::GetBaseFilename(File);
    Files.Sort(); return Files;
}

bool UCombatWorkbenchSubsystem::ExportTuningReport(const TArray<double>& V,const FString& Name,FString& Result)
{
    if(!SafeName(Name)) {Result=TEXT("이름: 영문·숫자·_·- 사용, 1~64자.");return false;}
    if(!ValidateValues(V,Result)) return false;
    const FString Dir=FPaths::ProjectSavedDir()/TEXT("CombatTuningReports");
    const FString Path=Dir/(Name+TEXT(".json"));
    if(IFileManager::Get().FileExists(*Path)) {Result=TEXT("같은 이름의 전달 파일이 있습니다. 새 이름을 입력하세요.");return false;}
    const auto Current=ReadValues();
    auto Root=MakeShared<FJsonObject>();
    Root->SetNumberField(TEXT("schema_version"),1);
    Root->SetStringField(TEXT("kind"),TEXT("ConstellationCombatTuningReport"));
    Root->SetStringField(TEXT("name"),Name);
    Root->SetStringField(TEXT("created_utc"),FDateTime::UtcNow().ToIso8601());
    Root->SetStringField(TEXT("value_basis"),TEXT("initial: 이 세션이 읽은 자산 초기값; current: 현재 전투 적용값; proposed: 내보내는 초안. 초안은 아직 적용되지 않았을 수 있습니다."));
    Root->SetStringField(TEXT("scope"),TEXT("전투 워크벤치의 전체 편집 항목. 애니메이션, 타격 노티파이, 지형, 카메라와 피해 기록은 포함하지 않습니다."));
    Root->SetStringField(TEXT("usage"),TEXT("AI 검토용 보고서이며 CombatRecipes 입력이 아닙니다. preset 객체는 기존 튜닝 프리셋 형식입니다. AI는 preset.values만 수정합니다. fields는 내보낸 당시의 참고 기록이며 불러오기에 사용하지 않습니다. 새 이름으로 저장한 뒤 게임에서 입력: AI 파일 → 불러오기 → 변경 내역 확인 → 적용합니다. 원본 자산을 자동 수정하지 않습니다."));
    Root->SetObjectField(TEXT("preset"),MakePresetDocument(V));
    TArray<TSharedPtr<FJsonValue>> Entries;
    int32 Changed=0,FromInitial=0;
    for(int32 I=0;I<Fields.Num();++I)
    {
        const auto& F=Fields[I];auto Entry=MakeShared<FJsonObject>();
        Entry->SetStringField(TEXT("key"),F.Key);
        Entry->SetStringField(TEXT("actor_key"),F.ActorKey);
        Entry->SetStringField(TEXT("role"),F.bEnemy?TEXT("monster"):TEXT("player"));
        Entry->SetStringField(TEXT("group"),F.Group);
        Entry->SetStringField(TEXT("label"),F.Label);
        Entry->SetStringField(TEXT("property"),F.Property.ToString());
        Entry->SetStringField(TEXT("value_type"),F.bBoolean?TEXT("boolean_0_1"):F.bInteger?TEXT("integer"):TEXT("number"));
        Entry->SetNumberField(TEXT("initial"),F.DefaultValue);
        Entry->SetNumberField(TEXT("current"),Current[I]);
        Entry->SetNumberField(TEXT("proposed"),V[I]);
        Entry->SetNumberField(TEXT("min"),F.Min);
        Entry->SetNumberField(TEXT("max"),F.Max);
        Entry->SetBoolField(TEXT("changed_from_current"),V[I]!=Current[I]);
        Entry->SetBoolField(TEXT("changed_from_initial"),V[I]!=F.DefaultValue);
        Changed+=V[I]!=Current[I];FromInitial+=V[I]!=F.DefaultValue;
        Entries.Add(MakeShared<FJsonValueObject>(Entry));
    }
    Root->SetArrayField(TEXT("fields"),Entries);
    Root->SetNumberField(TEXT("changed_from_current"),Changed);
    Root->SetNumberField(TEXT("changed_from_initial"),FromInitial);
    FString Json;
    if(!FJsonSerializer::Serialize(Root,TJsonWriterFactory<>::Create(&Json)))
    {Result=TEXT("전달 파일을 구성하지 못했습니다.");return false;}
    IFileManager::Get().MakeDirectory(*Dir,true);
    if(!FFileHelper::SaveStringToFile(Json,*Path,FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM,&IFileManager::Get(),FILEWRITE_NoReplaceExisting))
    {Result=TEXT("전달 파일을 저장하지 못했습니다.");return false;}
    Result=TEXT("AI 전달 파일: Saved/CombatTuningReports/")+Name+TEXT(".json");return true;
}

bool UCombatWorkbenchSubsystem::LoadTuningReport(const FString& Name,TArray<double>& V,FString& Error)
{
    if(!SafeName(Name)) {Error=TEXT("올바른 AI 파일 이름을 선택하세요.");return false;}
    FString Json,Kind;double Version=0;TSharedPtr<FJsonObject> Root;
    const TSharedPtr<FJsonObject>* Preset=nullptr;
    const FString Path=FPaths::ProjectSavedDir()/TEXT("CombatTuningReports")/(Name+TEXT(".json"));
    if(!FFileHelper::LoadFileToString(Json,*Path) ||
        !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Json),Root) || !Root.IsValid() ||
        !Root->HasTypedField<EJson::Number>(TEXT("schema_version")) || !Root->TryGetNumberField(TEXT("schema_version"),Version) || Version!=1 ||
        !Root->TryGetStringField(TEXT("kind"),Kind) || Kind!=TEXT("ConstellationCombatTuningReport") ||
        !Root->TryGetObjectField(TEXT("preset"),Preset))
    {Error=TEXT("AI 전달 파일 형식 또는 버전이 올바르지 않습니다.");return false;}
    return ReadPresetDocument(*Preset,V,Error);
}
TArray<FString> UCombatWorkbenchSubsystem::ListTuningReports() const
{
    TArray<FString> Files;
    IFileManager::Get().FindFiles(Files,*(FPaths::ProjectSavedDir()/TEXT("CombatTuningReports/*.json")),true,false);
    for(FString& File:Files) File=FPaths::GetBaseFilename(File);
    Files.Sort();return Files;
}
