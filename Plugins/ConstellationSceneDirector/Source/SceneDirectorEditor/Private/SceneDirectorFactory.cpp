#include "SceneDirectorFactory.h"
#include "SceneDirectorAsset.h"
USceneDirectorFactory::USceneDirectorFactory(){SupportedClass=USceneDirectorAsset::StaticClass();bCreateNew=true;bEditAfterNew=true;}
UObject* USceneDirectorFactory::FactoryCreateNew(UClass* Class,UObject* Parent,FName Name,EObjectFlags Flags,UObject*,FFeedbackContext*)
{
    auto* Asset=NewObject<USceneDirectorAsset>(Parent,Class,Name,Flags|RF_Transactional);
    FDirectorStep Start; Start.Type=EDirectorNodeType::Start;
    FDirectorStep Wait; Wait.Type=EDirectorNodeType::Wait; Wait.EditorPosition=FVector2D(270,0);
    FDirectorStep End; End.Type=EDirectorNodeType::End; End.EditorPosition=FVector2D(540,0);
    Start.NextNodes={Wait.Id};Wait.NextNodes={End.Id};Asset->Steps={Start,Wait,End};return Asset;
}
