// Copyright (c) 2024 Ynput s.r.o.
#include "AyonCommands.h"

#define LOCTEXT_NAMESPACE "FAyonModule"

void FAyonCommands::RegisterCommands()
{
	UI_COMMAND(AyonLoaderTool, "Load", "Open loader tool", EUserInterfaceActionType::Button, FInputChord());
	UI_COMMAND(AyonCreatorTool, "Create", "Open creator tool", EUserInterfaceActionType::Button, FInputChord());
	UI_COMMAND(AyonSceneInventoryTool, "Scene inventory", "Open scene inventory tool", EUserInterfaceActionType::Button, FInputChord());
	UI_COMMAND(AyonPublishTool, "Publish", "Open publisher", EUserInterfaceActionType::Button, FInputChord());
}

#undef LOCTEXT_NAMESPACE
