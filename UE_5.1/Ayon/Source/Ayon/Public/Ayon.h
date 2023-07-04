// Copyright (c) 2023 Ynput s.r.o.
#pragma once

#include "CoreMinimal.h"


class FAyonModule : public IModuleInterface
{
public:
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;

protected:
	static TSharedRef<SWidget> GenerateAyonMenuContent(TSharedRef<class FUICommandList> InCommandList);

	static void CallMethod(const FString MethodName, const TArray<FString> Args);

private:
	void RegisterMenus();
	void RegisterSettings();
	bool HandleSettingsSaved();

	void RegisterAyonMenu();
	void MapCommands();

private:
	TSharedPtr<class FUICommandList> PluginCommands;
};
