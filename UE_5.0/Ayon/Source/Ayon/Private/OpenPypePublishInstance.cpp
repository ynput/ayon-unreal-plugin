// Copyright (c) 2024 Ynput s.r.o.
// Deprecation warning: this is left here just for backwards compatibility
// and will be removed in next versions of Ayon.
#pragma once

#include "OpenPypePublishInstance.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetToolsModule.h"
#include "Framework/Notifications/NotificationManager.h"
#include "AyonLib.h"
#include "AyonSettings.h"
#include "Widgets/Notifications/SNotificationList.h"


//Moves all the invalid pointers to the end to prepare them for the shrinking
#define REMOVE_INVALID_ENTRIES(VAR) VAR.CompactStable(); \
									VAR.Shrink();

UOpenPypePublishInstance::UOpenPypePublishInstance(const FObjectInitializer& ObjectInitializer)
	: UPrimaryDataAsset(ObjectInitializer)
{
	const FAssetRegistryModule& AssetRegistryModule = FModuleManager::LoadModuleChecked<
		FAssetRegistryModule>("AssetRegistry");

	const FPropertyEditorModule& PropertyEditorModule = FModuleManager::LoadModuleChecked<FPropertyEditorModule>(
		"PropertyEditor");

	FString Left, Right;
	GetPathName().Split("/" + GetName(), &Left, &Right);

	FARFilter Filter;
	Filter.PackagePaths.Emplace(FName(Left));

	TArray<FAssetData> FoundAssets;
	AssetRegistryModule.GetRegistry().GetAssets(Filter, FoundAssets);

	for (const FAssetData& AssetData : FoundAssets)
		OnAssetCreated(AssetData);

	REMOVE_INVALID_ENTRIES(AssetDataInternal)
	REMOVE_INVALID_ENTRIES(AssetDataExternal)

	AssetRegistryModule.Get().OnAssetAdded().AddUObject(this, &UOpenPypePublishInstance::OnAssetCreated);
	AssetRegistryModule.Get().OnAssetRemoved().AddUObject(this, &UOpenPypePublishInstance::OnAssetRemoved);
	AssetRegistryModule.Get().OnAssetUpdated().AddUObject(this, &UOpenPypePublishInstance::OnAssetUpdated);

#ifdef WITH_EDITOR
	ColorOpenPypeDirs();
#endif
}

void UOpenPypePublishInstance::OnAssetCreated(const FAssetData& InAssetData)
{
	TArray<FString> split;

	UObject* Asset = InAssetData.GetAsset();

	if (!IsValid(Asset))
	{
		UE_LOG(LogAssetData, Warning, TEXT("Asset \"%s\" is not valid! Skipping the addition."),
		       *InAssetData.ObjectPath.ToString());
		return;
	}

	const bool result = IsUnderSameDir(Asset) && Cast<UOpenPypePublishInstance>(Asset) == nullptr;

	if (result)
	{
		if (AssetDataInternal.Emplace(Asset).IsValidId())
		{
			UE_LOG(LogTemp, Log, TEXT("Added an Asset to PublishInstance - Publish Instance: %s, Asset %s"),
			       *this->GetName(), *Asset->GetName());
		}
	}
}

void UOpenPypePublishInstance::OnAssetRemoved(const FAssetData& InAssetData)
{
	if (Cast<UOpenPypePublishInstance>(InAssetData.GetAsset()) == nullptr)
	{
		if (AssetDataInternal.Contains(nullptr))
		{
			AssetDataInternal.Remove(nullptr);
			REMOVE_INVALID_ENTRIES(AssetDataInternal)
		}
		else
		{
			AssetDataExternal.Remove(nullptr);
			REMOVE_INVALID_ENTRIES(AssetDataExternal)
		}
	}
}

void UOpenPypePublishInstance::OnAssetUpdated(const FAssetData& InAssetData)
{
	REMOVE_INVALID_ENTRIES(AssetDataInternal);
	REMOVE_INVALID_ENTRIES(AssetDataExternal);
}

bool UOpenPypePublishInstance::IsUnderSameDir(const UObject* InAsset) const
{
	FString ThisLeft, ThisRight;
	this->GetPathName().Split(this->GetName(), &ThisLeft, &ThisRight);

	return InAsset->GetPathName().StartsWith(ThisLeft);
}

#ifdef WITH_EDITOR

void UOpenPypePublishInstance::ColorOpenPypeDirs()
{
	FString PathName = this->GetPathName();

	//Check whether the path contains the defined OpenPype folder
	if (!PathName.Contains(TEXT("OpenPype"))) return;

	//Get the base path for open pype
	FString PathLeft, PathRight;
	PathName.Split(FString("OpenPype"), &PathLeft, &PathRight);

	if (PathLeft.IsEmpty() || PathRight.IsEmpty())
	{
		UE_LOG(LogAssetData, Error, TEXT("Failed to retrieve the base OpenPype directory!"))
		return;
	}

	PathName.RemoveFromEnd(PathRight, ESearchCase::CaseSensitive);

	//Get the current settings
	const UAyonSettings* Settings = GetMutableDefault<UAyonSettings>();

	//Color the base folder
	UAyonLib::SetFolderColor(PathName, Settings->GetFolderFColor(), false);

	//Get Sub paths, iterate through them and color them according to the folder color in UOpenPypeSettings
	const FAssetRegistryModule& AssetRegistryModule = FModuleManager::LoadModuleChecked<FAssetRegistryModule>(
		"AssetRegistry");

	TArray<FString> PathList;

	AssetRegistryModule.Get().GetSubPaths(PathName, PathList, true);

	if (PathList.Num() > 0)
	{
		for (const FString& Path : PathList)
		{
			UAyonLib::SetFolderColor(Path, Settings->GetFolderFColor(), false);
		}
	}
}

void UOpenPypePublishInstance::SendNotification(const FString& Text) const
{
	FNotificationInfo Info{FText::FromString(Text)};

	Info.bFireAndForget = true;
	Info.bUseLargeFont = false;
	Info.bUseThrobber = false;
	Info.bUseSuccessFailIcons = false;
	Info.ExpireDuration = 4.f;
	Info.FadeOutDuration = 2.f;

	FSlateNotificationManager::Get().AddNotification(Info);

	UE_LOG(LogAssetData, Warning,
	       TEXT(
		       "Removed duplicated asset from the AssetsDataExternal in Container \"%s\", Asset is already included in the AssetDataInternal!"
	       ), *GetName()
	)
}


void UOpenPypePublishInstance::PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent)
{
	Super::PostEditChangeProperty(PropertyChangedEvent);

	if (PropertyChangedEvent.ChangeType == EPropertyChangeType::ValueSet &&
		PropertyChangedEvent.Property->GetFName() == GET_MEMBER_NAME_CHECKED(
			UOpenPypePublishInstance, AssetDataExternal))
	{
		// Check for duplicated assets
		for (const auto& Asset : AssetDataInternal)
		{
			if (AssetDataExternal.Contains(Asset))
			{
				AssetDataExternal.Remove(Asset);
				return SendNotification(
					"You are not allowed to add assets into AssetDataExternal which are already included in AssetDataInternal!");
			}
		}

		// Check if no UOpenPypePublishInstance type assets are included
		for (const auto& Asset : AssetDataExternal)
		{
			if (Cast<UOpenPypePublishInstance>(Asset.Get()) != nullptr)
			{
				AssetDataExternal.Remove(Asset);
				return SendNotification("You are not allowed to add publish instances!");
			}
		}
	}
}

#endif
