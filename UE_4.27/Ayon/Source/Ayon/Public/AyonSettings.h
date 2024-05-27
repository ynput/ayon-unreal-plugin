// Copyright (c) 2024 Ynput s.r.o.

#pragma once

#include "CoreMinimal.h"
#include "AyonSettings.generated.h"

#define AYON_SETTINGS_FILEPATH IPluginManager::Get().FindPlugin("Ayon")->GetBaseDir() / TEXT("Config") / TEXT("DefaultAyonSettings.ini")

UCLASS(Config=AyonSettings, DefaultConfig)
class AYON_API UAyonSettings : public UObject
{
	GENERATED_UCLASS_BODY()

	UFUNCTION(BlueprintCallable, BlueprintPure, Category = Settings)
	FColor GetFolderFColor() const
	{
		return FolderColor;
	}

	UFUNCTION(BlueprintCallable, BlueprintPure, Category = Settings)
	FLinearColor GetFolderFLinearColor() const
	{
		return FLinearColor(FolderColor);
	}

protected:

	UPROPERTY(config, EditAnywhere, Category = Folders)
	FColor FolderColor = FColor(25,45,223);
};
