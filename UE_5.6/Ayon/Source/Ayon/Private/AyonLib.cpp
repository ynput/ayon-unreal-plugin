// Copyright (c) 2024 Ynput s.r.o.
#include "AyonLib.h"

#include "AssetViewUtils.h"
#include "UObject/UnrealType.h"

/**
 * Sets color on folder icon on given path
 * @param InPath - path to folder
 * @param InFolderColor - color of the folder
 * @warning This color will appear only after Editor restart. Is there a better way?
 */

bool UAyonLib::SetFolderColor(const FString& FolderPath, const FLinearColor& FolderColor, const bool& bForceAdd)
{
	if (AssetViewUtils::DoesFolderExist(FolderPath))
	{
		const TSharedPtr<FLinearColor> LinearColor = MakeShared<FLinearColor>(FolderColor);

		AssetViewUtils::SaveColor(FolderPath, LinearColor, true);
		UE_LOG(LogAssetData, Display, TEXT("A color {%s} has been set to folder \"%s\""), *LinearColor->ToString(),
		       *FolderPath)
		return true;
	}

	UE_LOG(LogAssetData, Display, TEXT("Setting a color {%s} to folder \"%s\" has failed! Directory doesn't exist!"),
	       *FolderColor.ToString(), *FolderPath)
	return false;
}

/**
 * Returns all poperties on  given object
 * @param cls - class
 * @return TArray of properties
 */
TArray<FString> UAyonLib::GetAllProperties(UClass* cls)
{
	TArray<FString> Ret;
	if (cls != nullptr)
	{
		for (TFieldIterator<FProperty> It(cls); It; ++It)
		{
			FProperty* Property = *It;
			if (Property->HasAnyPropertyFlags(EPropertyFlags::CPF_Edit))
			{
				Ret.Add(Property->GetName());
			}
		}
	}
	return Ret;
}
