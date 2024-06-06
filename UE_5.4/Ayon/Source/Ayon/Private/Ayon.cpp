// Copyright (c) 2024 Ynput s.r.o.
#include "Ayon.h"

#include "ISettingsContainer.h"
#include "ISettingsModule.h"
#include "ISettingsSection.h"
#include "IWebSocket.h"
#include "Framework/Commands/UICommandList.h"
#include "Modules/ModuleManager.h"
#include "Widgets/SWidget.h"
#include "AyonStyle.h"
#include "AyonCommands.h"
#include "AyonPythonBridge.h"
#include "AyonSettings.h"
#include "ToolMenus.h"


static const FName AyonTabName("Ayon");

#define LOCTEXT_NAMESPACE "FAyonModule"

// This function is triggered when the plugin is staring up
void FAyonModule::StartupModule()
{
	if(!FModuleManager::Get().IsModuleLoaded("WebSockets"))
	{
		FModuleManager::Get().LoadModule("WebSockets");
	}

	FAyonStyle::Initialize();
	FAyonStyle::ReloadTextures();
	FAyonCommands::Register();

	FAyonCommunication::CreateSocket();
	FAyonCommunication::ConnectToSocket();

	MapCommands();

	UToolMenus::RegisterStartupCallback(FSimpleMulticastDelegate::FDelegate::CreateRaw(this, &FAyonModule::RegisterMenus));

	RegisterSettings();
}

void FAyonModule::ShutdownModule()
{
	FAyonCommunication::CloseConnection();

	UToolMenus::UnRegisterStartupCallback(this);

	UToolMenus::UnregisterOwner(this);

	FAyonStyle::Shutdown();

	FAyonCommands::Unregister();
}

TSharedRef<SWidget> FAyonModule::GenerateAyonMenuContent(TSharedRef<FUICommandList> InCommandList)
{
	FToolMenuContext MenuContext(InCommandList);

	return UToolMenus::Get()->GenerateWidget("LevelEditor.LevelEditorToolBar.Ayon", MenuContext);
}

void FAyonModule::RegisterSettings()
{
	ISettingsModule& SettingsModule = FModuleManager::LoadModuleChecked<ISettingsModule>("Settings");

	// Create the new category
	// TODO: After the movement of the plugin from the game to editor, it might be necessary to move this!
	ISettingsContainerPtr SettingsContainer = SettingsModule.GetContainer("Project");

	UAyonSettings* Settings = GetMutableDefault<UAyonSettings>();

	// Register the settings
	ISettingsSectionPtr SettingsSection = SettingsModule.RegisterSettings("Project", "Ayon", "General",
	                                                                      LOCTEXT("RuntimeGeneralSettingsName",
		                                                                      "General"),
	                                                                      LOCTEXT("RuntimeGeneralSettingsDescription",
		                                                                      "Base configuration for Open Pype Module"),
	                                                                      Settings
	);

	// Register the save handler to your settings, you might want to use it to
	// validate those or just act to settings changes.
	if (SettingsSection.IsValid())
	{
		SettingsSection->OnModified().BindRaw(this, &FAyonModule::HandleSettingsSaved);
	}
}

bool FAyonModule::HandleSettingsSaved()
{
	UAyonSettings* Settings = GetMutableDefault<UAyonSettings>();
	bool ResaveSettings = false;

	// You can put any validation code in here and resave the settings in case an invalid
	// value has been entered

	if (ResaveSettings)
	{
		Settings->SaveConfig();
	}

	return true;
}

void FAyonModule::CallMethod(const FString MethodName, const TArray<FString> Args)
{
	FAyonCommunication::CallMethod(MethodName, Args);
}

void FAyonModule::RegisterMenus()
{
	// Owner will be used for cleanup in call to UToolMenus::UnregisterOwner
	FToolMenuOwnerScoped OwnerScoped(this);

	RegisterAyonMenu();

	UToolMenu* ToolbarMenu = UToolMenus::Get()->ExtendMenu("LevelEditor.LevelEditorToolBar.User");

	FToolMenuSection& Section = ToolbarMenu->AddSection("Ayon");

	FToolMenuEntry AyonEntry = FToolMenuEntry::InitComboButton(
		"Ayon Menu",
		FUIAction(),
		FOnGetContent::CreateStatic(&FAyonModule::GenerateAyonMenuContent, AyonCommands.ToSharedRef()),
		LOCTEXT("AyonMenu_Label", "Ayon"),
		LOCTEXT("AyonMenu_Tooltip", "Open Ayon Menu"),
		FSlateIcon(FAyonStyle::GetStyleSetName(), "Ayon.AyonMenu")
	);
	Section.AddEntry(AyonEntry);
}

void FAyonModule::RegisterAyonMenu()
{
	UToolMenu* AyonMenu = UToolMenus::Get()->RegisterMenu("LevelEditor.LevelEditorToolBar.Ayon");
	{
		FToolMenuSection& Section = AyonMenu->AddSection("Ayon");

		Section.InitSection("Ayon", LOCTEXT("Ayon_Label", "Ayon"), FToolMenuInsert(NAME_None, EToolMenuInsertType::First));

		Section.AddMenuEntry(FAyonCommands::Get().AyonLoaderTool);
		Section.AddMenuEntry(FAyonCommands::Get().AyonCreatorTool);
		Section.AddMenuEntry(FAyonCommands::Get().AyonSceneInventoryTool);
		Section.AddMenuEntry(FAyonCommands::Get().AyonPublishTool);
	}
}

void FAyonModule::MapCommands()
{
	AyonCommands = MakeShareable(new FUICommandList);

	AyonCommands->MapAction(
		FAyonCommands::Get().AyonLoaderTool,
		FExecuteAction::CreateStatic(&FAyonModule::CallMethod, FString("loader_tool"), TArray<FString>()),
		FCanExecuteAction());
	AyonCommands->MapAction(
		FAyonCommands::Get().AyonCreatorTool,
		FExecuteAction::CreateStatic(&FAyonModule::CallMethod, FString("creator_tool"), TArray<FString>()),
		FCanExecuteAction());
	AyonCommands->MapAction(
		FAyonCommands::Get().AyonSceneInventoryTool,
		FExecuteAction::CreateStatic(&FAyonModule::CallMethod, FString("scene_inventory_tool"), TArray<FString>()),
		FCanExecuteAction());
	AyonCommands->MapAction(
		FAyonCommands::Get().AyonPublishTool,
		FExecuteAction::CreateStatic(&FAyonModule::CallMethod, FString("publish_tool"), TArray<FString>()),
		FCanExecuteAction());
}

IMPLEMENT_MODULE(FAyonModule, Ayon)
