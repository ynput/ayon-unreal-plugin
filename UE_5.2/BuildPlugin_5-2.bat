:: Set or replace UNREAL_ENGINE_52 to
:: the location of your 5.2 installation.
:: AYON_ROOT (formely OPENPYPE_ROOT) should point
:: to AYON Desktop (OpenPype) sources.

SET UNREAL_ENGINE_52=%PROGRAMFILES%\Epic Games\UE_5.2
%UNREAL_ENGINE_52%\Engine\Build\BatchFiles\RunUAT.bat BuildPlugin -plugin=%AYON_ROOT%\openpype\hosts\unreal\integration\UE_5.2\Ayon\Ayon.uplugin" -Package="%~dp0..\build\UE_5.2"
