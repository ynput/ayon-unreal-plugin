:: Set or replace UNREAL_ENGINE_53 to
:: the location of your 5.3 installation.
:: AYON_ROOT (formely OPENPYPE_ROOT) should point
:: to AYON Desktop (OpenPype) sources.

SET UNREAL_ENGINE_53=%PROGRAMFILES%\Epic Games\UE_5.3
%UNREAL_ENGINE_53%\Engine\Build\BatchFiles\RunUAT.bat BuildPlugin -plugin=%AYON_UNREAL_ROOT%\integration\UE_5.3\Ayon\Ayon.uplugin" -Package="%~dp0..\build\UE_5.3"
