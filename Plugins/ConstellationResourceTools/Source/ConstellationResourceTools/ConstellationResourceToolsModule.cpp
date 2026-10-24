#include "Modules/ModuleManager.h"
#include "TextManagement/TextManagementIndex.h"
class FConstellationResourceToolsModule : public IModuleInterface
{
public:
    virtual void StartupModule() override { if(!IsRunningCommandlet())ConstellationText::RegisterTextManagement(); }
    virtual void ShutdownModule() override { if(!IsRunningCommandlet())ConstellationText::UnregisterTextManagement(); }
};
IMPLEMENT_MODULE(FConstellationResourceToolsModule,ConstellationResourceTools)
