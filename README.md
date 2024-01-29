AYON Unreal Integration Plugin
==============================

This repository holds the code for AYON Unreal integration plugin for various UE versions.

Documentation of how to use AYON integration inside Unreal is [here](https://ayon.ynput.io/docs/addon_unreal_artist).

This repository should be used as git submodule in [AYON Desktop / OpenPype](https://github.com/ynput/OpenPype)
sources under `/openpype/hosts/unreal/integration`. In the future, Unreal
integration will be moved to it's own AYON addon.

Getting started
---------------

This plugin meant to be used directly by AYON (OpenPype) either through Epic Marketplace or manually, when
new Unreal project is started via AYON.

For every supported Unreal version there is one plugin (**Ayon**) and one project (**CommandletProject**).

How it works
------------

When you launch Unreal Editor on any task through AYON, following things will happen:

- Environment is prepared.
- We check for presence of AYON plugin in Unreal Engine.
- If the plugin isn't found, AYON will try to build it. For this step you
will need configured build environment. Please follow [guides on Unreal documentation](https://docs.unrealengine.com/5.0/en-US/setting-up-your-development-environment-for-cplusplus-in-unreal-engine/) for more information.
- **CommandletProject** is blank project that is used to bootstrap project
creation by Unreal Editor itself.
- Unreal Editor is launched on new generated project.

Integration plugin is providing UI access to AYON functionality. Most of
the code is used to mark and define data structures used by AYON inside
Editor itself, rest of the functionality is implemented in Python inside
AYON codebase.

Manual build
------------

You can used provided Windows batch scripts to build plugin manually.

In order to successfully build the plugin, make sure that the path to the `UnrealBuildTool.exe` is specified correctly.

After the UBT path specify for which platform it will be compiled. in the `-Project` parameter, specify the path to the `CommandletProject.uproject` file. Next the build type has to be specified (*DebugGame*, *Development*, *Package*, etc.) and then the `-TargetType` (*Editor*, *Runtime*, etc.)

`BuildPlugin_[Ver].bat` runs the building process in the background. If you want to show the progress inside the command prompt, use the `BuildPlugin_[Ver]_Window.bat` file.

Related links
--------------------

- **AYON Desktop** / **Openpype** repository: [https://github.com/ynput/OpenPype](https://github.com/ynput/OpenPype)
- **Unreal Engine**: [https://www.unrealengine.com/](https://www.unrealengine.com/)
- **AYON / OpenPype** help: [https://ayon.ynput.io/](https://ayon.ynput.io/)
- **AYON Docker** repository: [https://github.com/ynput/ayon-docker](https://github.com/ynput/ayon-docker)
- [Development Setup guides for Unreal](https://docs.unrealengine.com/5.0/en-US/setting-up-your-development-environment-for-cplusplus-in-unreal-engine/)
