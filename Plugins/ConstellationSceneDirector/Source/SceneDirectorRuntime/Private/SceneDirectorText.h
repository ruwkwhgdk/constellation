#pragma once
#include "Engine/DataTable.h"

namespace DirectorText
{
    bool Validate(const FDataTableRowHandle& Handle,FString& Error);
    FText Resolve(const FDataTableRowHandle& Handle,const FText& Direct);
}
