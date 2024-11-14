:: Set or replace UNREAL_ENGINE_55 to
:: the location of your 5.5 installation.
:: AYON_UNREAL_ROOT should point to unreal addon root

SET UNREAL_ENGINE_55=%PROGRAMFILES%\Epic Games\UE_5.5
%UNREAL_ENGINE_55%\Engine\Build\BatchFiles\RunUAT.bat BuildPlugin -plugin=%AYON_UNREAL_ROOT%\integration\UE_5.5\Ayon\Ayon.uplugin" -Package="%~dp0..\build\UE_5.5"
