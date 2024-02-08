:: Set or replace UNREAL_ENGINE_53 to
:: the location of your 5.3 installation.
:: AYON_UNREAL_ROOT should point to unreal addon root

SET UNREAL_ENGINE_53=%PROGRAMFILES%\Epic Games\UE_5.3
%UNREAL_ENGINE_53%\Engine\Build\BatchFiles\RunUAT.bat BuildPlugin -plugin=%AYON_UNREAL_ROOT%\integration\UE_5.3\Ayon\Ayon.uplugin" -Package="%~dp0..\build\UE_5.3"
