// Copyright (c) 2024 Ynput s.r.o.

#include "AyonCommands.h"

#define LOCTEXT_NAMESPACE "FAyonModule"

void FAyonCommands::RegisterCommands()
{
	UI_COMMAND(AyonTools, "Ayon Tools", "Pipeline tools", EUserInterfaceActionType::Button, FInputChord());
	UI_COMMAND(AyonToolsDialog, "Ayon Tools Dialog", "Pipeline tools dialog", EUserInterfaceActionType::Button, FInputChord());
}

#undef LOCTEXT_NAMESPACE
