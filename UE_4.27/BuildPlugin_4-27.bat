:: Set or replace UNREAL_ENGINE_427 to
:: the location of your 4.27 installation.
:: AYON_ROOT (formely OPENPYPE_ROOT) should point
:: to AYON Desktop (OpenPype) sources.

SET UNREAL_ENGINE_427=%PROGRAMFILES%\Epic Games\UE_4.27
%UNREAL_ENGINE_427%\Engine\Build\BatchFiles\RunUAT.bat BuildPlugin -plugin=%AYON_ROOT%\openpype\hosts\unreal\integration\UE_4.27\Ayon\Ayon.uplugin" -Package="%~dp0..\build\UE_4.27\Ayon"
