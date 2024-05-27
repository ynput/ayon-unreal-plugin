// Copyright (c) 2024 Ynput s.r.o.

#include "AyonSettings.h"

#include "Interfaces/IPluginManager.h"
#include "UObject/UObjectGlobals.h"

/**
 * Mainly is used for initializing default values if the DefaultAyonSettings.ini file does not exist in the saved config
 */
UAyonSettings::UAyonSettings(const FObjectInitializer& ObjectInitializer)
{
	
	const FString ConfigFilePath = AYON_SETTINGS_FILEPATH;

	// This has to be probably in the future set using the UE Reflection system
	FColor Color;
	GConfig->GetColor(TEXT("/Script/Ayon.AyonSettings"), TEXT("FolderColor"), Color, ConfigFilePath);

	FolderColor = Color;
}