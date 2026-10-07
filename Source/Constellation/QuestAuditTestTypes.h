#pragma once

#include "QuestDefinition.h"
#include "QuestDatabase.h"
#include "QuestSubsystem.h"
#include "QuestAuditTestTypes.generated.h"

UCLASS(Transient, NotBlueprintable)
class UQuestAuditReentrantDefinition : public UQuestDefinition
{
    GENERATED_BODY()
public:
    UPROPERTY()
    TObjectPtr<UQuestSubsystem> Subsystem;
    UPROPERTY()
    TObjectPtr<UQuestDatabase> Database;
    mutable int32 Calls = 0;

    virtual bool CheckCustomUnlockCondition_Implementation(const UObject*) const override
    {
        // Bound the fixture so a regression fails an assertion instead of overflowing the stack.
        if (++Calls < 4)
        {
            Subsystem->RegisterQuestDatabase(Database);
        }
        return true;
    }
};
