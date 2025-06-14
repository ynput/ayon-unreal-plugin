// Copyright (c) 2025 Ynput s.r.o.

using UnrealBuildTool;

public class Ayon : ModuleRules
{
	public Ayon(ReadOnlyTargetRules Target) : base(Target)
	{
	    DefaultBuildSettings = BuildSettingsVersion.V2;
	    bLegacyPublicIncludePaths = false;
	    ShadowVariableWarningLevel = WarningLevel.Error;
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;
		//IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_0;
		
		PublicIncludePaths.AddRange(
			new string[] {
				// ... add public include paths required here ...
			}
			);
				
		
		PrivateIncludePaths.AddRange(
			new string[] {
				// ... add other private include paths required here ...
			}
			);
			
		
		PublicDependencyModuleNames.AddRange(
			new string[]
			{
				"Core",
				"CoreUObject"
				// ... add other public dependencies that you statically link with here ...
			}
			);
		
		PrivateDependencyModuleNames.AddRange(
			new string[]
			{
				"GameProjectGeneration",
				"Projects",
				"InputCore",
				"EditorFramework",
				"UnrealEd",
				"ToolMenus",
				"LevelEditor",
				"CoreUObject",
				"Engine",
				"Slate",
				"SlateCore",
				"AssetTools"
				// ... add private dependencies that you statically link with here ...	
			}
			);
		
		
		DynamicallyLoadedModuleNames.AddRange(
			new string[]
			{
				// ... add any modules that your module loads dynamically here ...
			}
			);
	}
}
