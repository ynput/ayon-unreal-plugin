from pathlib import Path

import unreal

from helpers import (
    get_params,
    format_string,
    get_asset,
    get_subsequences
)
from pipeline import (
    UNREAL_VERSION,
    ls,
)


def create_look(params):
    """
    Args:
        params (str): string containing a dictionary with parameters:
            path (str): path to the instance
            selected_asset (str): path to the selected asset
    """
    path, selected_asset = get_params(params, 'path', 'selected_asset')

    # Create a new cube static mesh
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    cube = ar.get_asset_by_object_path("/Engine/BasicShapes/Cube.Cube")

    # Get the mesh of the selected object
    original_mesh = ar.get_asset_by_object_path(selected_asset).get_asset()
    materials = original_mesh.get_editor_property('static_materials')

    members = []

    # Add the materials to the cube
    for material in materials:
        mat_name = material.get_editor_property('material_slot_name')
        object_path = f"{path}/{mat_name}.{mat_name}"
        unreal_object = unreal.EditorAssetLibrary.duplicate_loaded_asset(
            cube.get_asset(), object_path
        )

        # Remove the default material of the cube object
        unreal_object.get_editor_property('static_materials').pop()

        unreal_object.add_material(
            material.get_editor_property('material_interface'))

        members.append(object_path)

        unreal.EditorAssetLibrary.save_asset(object_path)

    return {"return": members}


def create_render_with_new_sequence(params):
    """
    Args:
        params (str): string containing a dictionary with parameters:
            selected_asset_path (str): path to the selected asset
            use_hierarchy (bool): whether to use the hierarchy
    """

    sequence_dir, subset_name, start_frame, end_frame = get_params(
        params, 'sequence_dir', 'subset_name', 'start_frame', 'end_frame')

    # Create a new folder for the sequence in root
    unreal.EditorAssetLibrary.make_directory(sequence_dir)

    unreal.log_warning(f"sequence_dir: {sequence_dir}")

    # Create the level sequence
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    seq = asset_tools.create_asset(
        asset_name=subset_name,
        package_path=sequence_dir,
        asset_class=unreal.LevelSequence,
        factory=unreal.LevelSequenceFactoryNew())

    seq.set_playback_start(start_frame)
    seq.set_playback_end(end_frame)

    unreal.EditorAssetLibrary.save_asset(seq.get_path_name())

    # Create the master level
    if UNREAL_VERSION.major >= 5:
        curr_level = unreal.LevelEditorSubsystem().get_current_level()
    else:
        world = unreal.EditorLevelLibrary.get_editor_world()
        levels = unreal.EditorLevelUtils.get_levels(world)
        curr_level = levels[0] if len(levels) else None
        if not curr_level:
            raise RuntimeError("No level loaded.")
    curr_level_path = curr_level.get_outer().get_path_name()

    # If the level path does not start with "/Game/", the current
    # level is a temporary, unsaved level.
    if curr_level_path.startswith("/Game/"):
        if UNREAL_VERSION.major >= 5:
            unreal.LevelEditorSubsystem().save_current_level()
        else:
            unreal.EditorLevelLibrary.save_current_level()

    ml_path = f"{sequence_dir}/{subset_name}_MasterLevel"

    if UNREAL_VERSION.major >= 5:
        unreal.LevelEditorSubsystem().new_level(ml_path)
    else:
        unreal.EditorLevelLibrary.new_level(ml_path)

    seq_data = {
        "sequence": seq,
        "output": f"{seq.get_name()}",
        "frame_range": (
            seq.get_playback_start(),
            seq.get_playback_end())}

    return ml_path, seq.get_path_name(), seq_data


def create_render_from_existing_sequence(params):
    """
    Args:
        params (str): string containing a dictionary with parameters:
            selected_asset_path (str): path to the selected asset
            use_hierarchy (bool): whether to use the hierarchy
    """
    selected_asset_path, use_hierarchy = get_params(
        params, 'selected_asset_path', 'use_hierarchy')

    ar = unreal.AssetRegistryHelpers.get_asset_registry()

    selected_asset = ar.get_asset_by_object_path(
        selected_asset_path).get_asset()

    # Check if the selected asset is a level sequence asset.
    if selected_asset.get_class().get_name() != "LevelSequence":
        unreal.log_warning(
            f"Skipping {selected_asset.get_name()}. It isn't a Level Sequence."
        )

    if use_hierarchy:
        # The asset name is the third element of the path which
        # contains the map.
        # To take the asset name, we remove from the path the prefix
        # "/Game/Ayon/" and then we split the path by "/".
        sel_path = selected_asset_path
        asset_name = sel_path.replace("/Game/Ayon/", "").split("/")[0]

        search_path = f"/Game/Ayon/{asset_name}"
    else:
        search_path = Path(selected_asset_path).parent.as_posix()

    # Get the master sequence and the master level.
    # There should be only one sequence and one level in the directory.
    try:
        ar_filter = unreal.ARFilter(
            class_names=["LevelSequence"],
            package_paths=[search_path],
            recursive_paths=False)
        sequences = ar.get_assets(ar_filter)
        master_seq = sequences[0].get_asset().get_path_name()
        master_seq_obj = sequences[0].get_asset()
        ar_filter = unreal.ARFilter(
            class_names=["World"],
            package_paths=[search_path],
            recursive_paths=False)
        levels = ar.get_assets(ar_filter)
        master_lvl = levels[0].get_asset().get_path_name()
    except IndexError as e:
        raise RuntimeError(
            "Could not find the hierarchy for the selected sequence."
        ) from e

    # If the selected asset is the master sequence, we get its data
    # and then we create the instance for the master sequence.
    # Otherwise, we cycle from the master sequence to find the selected
    # sequence and we get its data. This data will be used to create
    # the instance for the selected sequence. In particular,
    # we get the frame range of the selected sequence and its final
    # output path.
    master_seq_data = {
        "sequence": master_seq_obj,
        "output": f"{master_seq_obj.get_name()}",
        "frame_range": (
            master_seq_obj.get_playback_start(),
            master_seq_obj.get_playback_end())}

    if selected_asset_path == master_seq or use_hierarchy:
        return master_seq, master_lvl, master_seq_data

    seq_data_list = [master_seq_data]

    for seq in seq_data_list:
        subscenes = get_subsequences(seq.get('sequence'))

        for sub_seq in subscenes:
            sub_seq_obj = sub_seq.get_sequence()
            curr_data = {
                "sequence": sub_seq_obj,
                "output": (f"{seq.get('output')}/"
                           f"{sub_seq_obj.get_name()}"),
                "frame_range": (
                    sub_seq.get_start_frame(),
                    sub_seq.get_end_frame() - 1)}

            # If the selected asset is the current sub-sequence,
            # we get its data and we break the loop.
            # Otherwise, we add the current sub-sequence data to
            # the list of sequences to check.
            if sub_seq_obj.get_path_name() == selected_asset_path:
                return master_seq, master_lvl, master_seq_data

            seq_data_list.append(curr_data)

    return None, None, None


def create_unique_asset_name(params):
    """
    Args:
        params (str): string containing a dictionary with parameters:
            root (str): root path of the asset
            asset (str): name of the asset
            name (str): name of the subset
            version (int): version of the subset
            suffix (str): suffix of the asset
    """
    root, asset, name, version, suffix = get_params(
        params, 'root', 'asset', 'name', 'version', 'suffix')

    if not suffix:
        suffix = ""

    tools = unreal.AssetToolsHelpers().get_asset_tools()
    subset = f"{name}_v{version:03d}" if version else name
    return {"return": tools.create_unique_asset_name(
        f"{root}/{asset}/{subset}", suffix)}


def get_current_level():
    curr_level = (unreal.LevelEditorSubsystem().get_current_level()
                  if UNREAL_VERSION >= 5
                  else unreal.EditorLevelLibrary.get_editor_world())

    curr_level_path = curr_level.get_outer().get_path_name()
    # If the level path does not start with "/Game/", the current
    # level is a temporary, unsaved level.
    return {
        "return": curr_level_path
        if curr_level_path.startswith("/Game/") else None}


def add_level_to_world(params):
    """
    Args:
        params (str): string containing a dictionary with parameters:
            level_path (str): path to the level
    """
    level_path = get_params(params, 'level_path')

    unreal.EditorLevelUtils.add_level_to_world(
        unreal.EditorLevelLibrary.get_editor_world(),
        level_path,
        unreal.LevelStreamingDynamic
    )


def list_assets(params):
    """
    Args:
        params (str): string containing a dictionary with parameters:
            directory_path (str): path to the directory
            recursive (bool): whether to list assets recursively
            include_folder (bool): whether to include folders
    """
    directory_path, recursive, include_folder = get_params(
        params, 'directory_path', 'recursive', 'include_folder')

    return {"return": list(unreal.EditorAssetLibrary.list_assets(
        directory_path, recursive, include_folder))}


def get_assets_of_class(params):
    """
    Args:
        params (str): string containing a dictionary with parameters:
            asset_list (list): list of assets
            class_name (str): name of the class
    """
    asset_list, class_name = get_params(params, 'asset_list', 'class_name')

    assets = []
    for asset in asset_list:
        if unreal.EditorAssetLibrary.does_asset_exist(asset):
            asset_object = unreal.EditorAssetLibrary.load_asset(asset)
            if asset_object.get_class().get_name() == class_name:
                assets.append(asset)
    return {"return": assets}


def get_all_assets_of_class(params):
    """
    Args:
        params (str): string containing a dictionary with parameters:
            class_name (str): name of the class
            path (str): path to the directory
            recursive (bool): whether to list assets recursively
    """
    class_name, path, recursive = get_params(
        params, 'class_name', 'path', 'recursive')

    ar = unreal.AssetRegistryHelpers.get_asset_registry()

    ar_filter = unreal.ARFilter(
        class_names=[class_name],
        package_paths=[path],
        recursive_paths=recursive)

    assets = ar.get_assets(ar_filter)

    return {
        "return": [str(asset.get_editor_property('object_path'))
                   for asset in assets]}


def get_first_asset_of_class(params):
    """
    Args:
        params (str): string containing a dictionary with parameters:
            class_name (str): name of the class
            path (str): path to the directory
            recursive (bool): whether to list assets recursively
    """
    return get_all_assets_of_class(params)[0]


def _get_first_asset_of_class(class_name, path, recursive):
    """
    Args:
        class_name (str): name of the class
        path (str): path to the directory
        recursive (bool): whether to list assets recursively
    """
    return get_first_asset_of_class(format_string(str({
        "class_name": class_name,
        "path": path,
        "recursive": recursive}))).get('return')


def save_listed_assets(params):
    """
    Args:
        params (str): string containing a dictionary with parameters:
            asset_list (list): list of assets
    """
    asset_list = get_params(params, 'asset_list')

    for asset in asset_list:
        unreal.EditorAssetLibrary.save_asset(asset)


def _import(
    filename, destination_path, destination_name, replace_existing,
    automated, save, options, options_properties, options_extra_properties
):
    """
    Args:
        filename (str): path to the file
        destination_path (str): path to the destination
        destination_name (str): name of the destination
        replace_existing (bool): whether to replace existing assets
        automated (bool): whether to import the asset automatically
        save (bool): whether to save the asset
        options: options for the import
        options_properties (list): list of properties for the options
        options_extra_properties (list): list of extra properties for the
            options
    """
    task = unreal.AssetImportTask()

    task.set_editor_property('filename', filename)
    task.set_editor_property('destination_path', destination_path)
    task.set_editor_property('destination_name', destination_name)
    task.set_editor_property('replace_existing', replace_existing)
    task.set_editor_property('automated', automated)
    task.set_editor_property('save', save)

    for prop in options_properties:
        options.set_editor_property(prop[0], eval(prop[1]))

    for prop in options_extra_properties:
        options.get_editor_property(prop[0]).set_editor_property(
            prop[1], eval(prop[2]))

    task.options = options

    return task


def import_abc_task(params):
    """
    Args:
        params (str): string containing a dictionary with parameters:
            filename (str): path to the file
            destination_path (str): path to the destination
            destination_name (str): name of the file
            replace_existing (bool): whether to replace existing assets
            automated (bool): whether to run the task automatically
            save (bool): whether to save the asset
            options_properties (list): list of properties for the options
            sub_options_properties (list): list of properties that require
                extra processing
            conversion_settings (dict): dictionary of conversion settings
    """
    (filename, destination_path, destination_name, replace_existing,
     automated, save, options_properties, sub_options_properties,
     conversion_settings) = get_params(
        params, 'filename', 'destination_path', 'destination_name',
        'replace_existing', 'automated', 'save', 'options_properties',
        'sub_options_properties', 'conversion_settings')

    task = _import(
        filename, destination_path, destination_name, replace_existing,
        automated, save, unreal.AbcImportSettings(),
        options_properties, sub_options_properties)

    if conversion_settings:
        conversion = unreal.AbcConversionSettings(
            preset=unreal.AbcConversionPreset.CUSTOM,
            flip_u=conversion_settings.get("flip_u"),
            flip_v=conversion_settings.get("flip_v"),
            rotation=conversion_settings.get("rotation"),
            scale=conversion_settings.get("scale"))

        task.options.conversion_settings = conversion

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])


def import_fbx_task(params):
    """
    Args:
        params (str): string containing a dictionary with parameters:
            task_properties (list): list of properties for the task
            options_properties (list): list of properties for the options
            options_extra_properties (list): list of extra properties for the
                options
    """
    (filename, destination_path, destination_name, replace_existing,
     automated, save, options_properties, sub_options_properties) = get_params(
        params, 'filename', 'destination_path', 'destination_name',
        'replace_existing', 'automated', 'save', 'options_properties',
        'sub_options_properties')

    task = _import(
        filename, destination_path, destination_name, replace_existing,
        automated, save, unreal.FbxImportUI(),
        options_properties, sub_options_properties)

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])


def get_sequence_frame_range(params):
    """
    Args:
        params (str): string containing a dictionary with parameters:
            sequence_path (str): path to the sequence
    """
    sequence_path = get_params(params, 'sequence_path')

    sequence = get_asset(sequence_path)
    return {"return": (
        sequence.get_playback_start(), sequence.get_playback_end())}


def _set_sequence_hierarchy(
    seq_i_path, seq_j_path, max_frame_i, min_frame_j, max_frame_j, map_paths
):
    seq_i = get_asset(seq_i_path)
    seq_j = get_asset(seq_j_path)

    # Get existing sequencer tracks or create them if they don't exist
    tracks = seq_i.get_master_tracks()
    subscene_track = None
    visibility_track = None
    for t in tracks:
        if t.get_class() == unreal.MovieSceneSubTrack.static_class():
            subscene_track = t
        if (t.get_class() ==
                unreal.MovieSceneLevelVisibilityTrack.static_class()):
            visibility_track = t
    if not subscene_track:
        subscene_track = seq_i.add_master_track(unreal.MovieSceneSubTrack)
    if not visibility_track:
        visibility_track = seq_i.add_master_track(
            unreal.MovieSceneLevelVisibilityTrack)

    # Create the sub-scene section
    subscenes = subscene_track.get_sections()
    subscene = None
    for s in subscenes:
        if s.get_editor_property('sub_sequence') == seq_j:
            subscene = s
            break
    if not subscene:
        subscene = subscene_track.add_section()
        subscene.set_row_index(len(subscene_track.get_sections()))
        subscene.set_editor_property('sub_sequence', seq_j)
        subscene.set_range(
            min_frame_j,
            max_frame_j + 1)

    # Create the visibility section
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    maps = []
    for m in map_paths:
        # Unreal requires to load the level to get the map name
        unreal.EditorLevelLibrary.save_all_dirty_levels()
        unreal.EditorLevelLibrary.load_level(m)
        maps.append(str(ar.get_asset_by_object_path(m).asset_name))

    vis_section = visibility_track.add_section()
    index = len(visibility_track.get_sections())

    vis_section.set_range(
        min_frame_j,
        max_frame_j + 1)
    vis_section.set_visibility(unreal.LevelVisibility.VISIBLE)
    vis_section.set_row_index(index)
    vis_section.set_level_names(maps)

    if min_frame_j > 1:
        hid_section = visibility_track.add_section()
        hid_section.set_range(
            1,
            min_frame_j)
        hid_section.set_visibility(unreal.LevelVisibility.HIDDEN)
        hid_section.set_row_index(index)
        hid_section.set_level_names(maps)
    if max_frame_j < max_frame_i:
        hid_section = visibility_track.add_section()
        hid_section.set_range(
            max_frame_j + 1,
            max_frame_i + 1)
        hid_section.set_visibility(unreal.LevelVisibility.HIDDEN)
        hid_section.set_row_index(index)
        hid_section.set_level_names(maps)


def generate_sequence(params):
    """
    Args:
        params (str): string containing a dictionary with parameters:
            asset_name (str): name of the sequence
            asset_path (str): path to the sequence
            start_frame (int): start frame of the sequence
            end_frame (int): end frame of the sequence
            fps (int): frames per second
    """
    asset_name, asset_path, start_frame, end_frame, fps = get_params(
        params, 'asset_name', 'asset_path', 'start_frame', 'end_frame', 'fps')

    tools = unreal.AssetToolsHelpers().get_asset_tools()

    sequence = tools.create_asset(
        asset_name=asset_name,
        package_path=asset_path,
        asset_class=unreal.LevelSequence,
        factory=unreal.LevelSequenceFactoryNew()
    )

    sequence.set_display_rate(unreal.FrameRate(fps, 1.0))
    sequence.set_playback_start(start_frame)
    sequence.set_playback_end(end_frame)

    sequence.set_work_range_start(start_frame / fps)
    sequence.set_work_range_end(end_frame / fps)
    sequence.set_view_range_start(start_frame / fps)
    sequence.set_view_range_end(end_frame / fps)

    tracks = sequence.get_master_tracks()
    track = None
    for t in tracks:
        if t.get_class().get_name() == "MovieSceneCameraCutTrack":
            track = t
            break
    if not track:
        track = sequence.add_master_track(unreal.MovieSceneCameraCutTrack)

    return {"return": sequence.get_path_name()}


def generate_camera_sequence(params):
    """
    Args:
        params (str): string containing a dictionary with parameters:
    """
    (asset, asset_dir, sequences, frame_ranges, level, fps, clip_in,
     clip_out) = get_params(
        params, 'asset', 'asset_dir', 'sequences', 'frame_ranges', 'level',
        'fps', 'clip_in', 'clip_out')

    tools = unreal.AssetToolsHelpers().get_asset_tools()
    cam_seq = tools.create_asset(
        asset_name=f"{asset}_camera",
        package_path=asset_dir,
        asset_class=unreal.LevelSequence,
        factory=unreal.LevelSequenceFactoryNew()
    )

    # Add sequences data to hierarchy
    for i in range(len(sequences) - 1):
        _set_sequence_hierarchy(
            sequences[i], sequences[i + 1],
            frame_ranges[i][1],
            frame_ranges[i + 1][0], frame_ranges[i + 1][1],
            [level])

    cam_seq.set_display_rate(unreal.FrameRate(fps, 1.0))
    cam_seq.set_playback_start(clip_in)
    cam_seq.set_playback_end(clip_out + 1)
    _set_sequence_hierarchy(
        sequences[-1], cam_seq.get_path_name(),
        frame_ranges[-1][1],
        clip_in, clip_out,
        [level])

    return {"return": cam_seq.get_path_name()}


def generate_layout_sequence(params):
    """
    Args:
        params (str): string containing a dictionary with parameters:
    """
    (asset, asset_dir, sequences, frame_ranges, level, fps, clip_in,
     clip_out) = get_params(
        params, 'asset', 'asset_dir', 'sequences', 'frame_ranges', 'level',
        'fps', 'clip_in', 'clip_out')

    tools = unreal.AssetToolsHelpers().get_asset_tools()
    sequence = tools.create_asset(
        asset_name=f"{asset}",
        package_path=asset_dir,
        asset_class=unreal.LevelSequence,
        factory=unreal.LevelSequenceFactoryNew()
    )

    # Add sequences data to hierarchy
    for i in range(len(sequences) - 1):
        _set_sequence_hierarchy(
            sequences[i], sequences[i + 1],
            frame_ranges[i][1],
            frame_ranges[i + 1][0], frame_ranges[i + 1][1],
            [level])

    sequence.set_display_rate(unreal.FrameRate(fps, 1.0))
    sequence.set_playback_start(0)
    sequence.set_playback_end(clip_out - clip_in + 1)
    _set_sequence_hierarchy(
        sequences[-1], sequence.get_path_name(),
        frame_ranges[-1][1],
        clip_in, clip_out,
        [level])

    return {"return": sequence.get_path_name()}


def get_current_sequence_and_level_info():
    from unreal import LevelSequenceEditorBlueprintLibrary as LevelSequenceLib

    curr_level_sequence = LevelSequenceLib.get_current_level_sequence()
    sequence_path = (
        curr_level_sequence.get_path_name() if curr_level_sequence else None)
    curr_time = LevelSequenceLib.get_current_time()
    is_cam_lock = LevelSequenceLib.is_camera_cut_locked_to_viewport()

    editor_subsystem = unreal.UnrealEditorSubsystem()
    vp_loc, vp_rot = editor_subsystem.get_level_viewport_camera_info()

    return {
        "return": (
            sequence_path,
            curr_time,
            is_cam_lock,
            [vp_loc.x, vp_loc.y, vp_loc.z],
            [vp_rot.roll, vp_rot.pitch, vp_rot.yaw])}


def set_current_sequence_and_level_info(params):
    sequence_path, curr_time, is_cam_lock, vp_loc, vp_rot = get_params(
        params, 'sequence_path', 'curr_time', 'is_cam_lock', 'vp_loc',
        'vp_rot')

    from unreal import LevelSequenceEditorBlueprintLibrary as LevelSequenceLib

    if sequence_path:
        curr_level_sequence = get_asset(sequence_path)

        LevelSequenceLib.open_level_sequence(curr_level_sequence)
        LevelSequenceLib.set_current_time(curr_time)
        LevelSequenceLib.set_lock_camera_cut_to_viewport(is_cam_lock)

    editor_subsystem = unreal.UnrealEditorSubsystem()
    editor_subsystem.set_level_viewport_camera_info(
        unreal.Vector(vp_loc[0], vp_loc[1], vp_loc[2]),
        unreal.Rotator(vp_rot[0], vp_rot[1], vp_rot[2]))


def update_camera(params):
    """
    Args:
        params (str): string containing a dictionary with parameters:
            asset_dir (str): path to the asset directory
            asset (str): name of the asset
            root (str): root path of the asset
    """
    asset_dir, asset, root = get_params(params, 'asset_dir', 'asset', 'root')

    ar = unreal.AssetRegistryHelpers.get_asset_registry()

    unreal.EditorLevelLibrary.save_current_level()

    _filter = unreal.ARFilter(
        class_names=["LevelSequence"],
        package_paths=[asset_dir],
        recursive_paths=False)
    sequences = ar.get_assets(_filter)
    _filter = unreal.ARFilter(
        class_names=["World"],
        package_paths=[asset_dir],
        recursive_paths=True)
    maps = ar.get_assets(_filter)

    # There should be only one map in the list
    unreal.EditorLevelLibrary.load_level(maps[0].get_asset().get_path_name())

    level_sequence = sequences[0].get_asset()

    display_rate = level_sequence.get_display_rate()
    playback_start = level_sequence.get_playback_start()
    playback_end = level_sequence.get_playback_end()

    sequence_name = f"{asset}_camera"

    # Get the actors in the level sequence.
    objs = unreal.SequencerTools.get_bound_objects(
        unreal.EditorLevelLibrary.get_editor_world(),
        level_sequence,
        level_sequence.get_bindings(),
        unreal.SequencerScriptingRange(
            has_start_value=True,
            has_end_value=True,
            inclusive_start=level_sequence.get_playback_start(),
            exclusive_end=level_sequence.get_playback_end()
        )
    )

    # Delete actors from the map
    for o in objs:
        if o.bound_objects[0].get_class().get_name() == "CineCameraActor":
            actor_path = o.bound_objects[0].get_path_name().split(":")[-1]
            actor = unreal.EditorLevelLibrary.get_actor_reference(actor_path)
            unreal.EditorLevelLibrary.destroy_actor(actor)

    # Remove the Level Sequence from the parent.
    # We need to traverse the hierarchy from the master sequence to find
    # the level sequence.
    namespace = asset_dir.replace(f"{root}/", "")
    ms_asset = namespace.split('/')[0]
    _filter = unreal.ARFilter(
        class_names=["LevelSequence"],
        package_paths=[f"{root}/{ms_asset}"],
        recursive_paths=False)
    sequences = ar.get_assets(_filter)
    master_sequence = sequences[0].get_asset()

    sequences = [master_sequence]

    parent = None
    sub_scene = None
    for s in sequences:
        tracks = s.get_master_tracks()
        subscene_track = None
        for t in tracks:
            if t.get_class() == unreal.MovieSceneSubTrack.static_class():
                subscene_track = t
        if subscene_track:
            sections = subscene_track.get_sections()
            for ss in sections:
                if ss.get_sequence().get_name() == sequence_name:
                    parent = s
                    sub_scene = ss
                    break
                sequences.append(ss.get_sequence())
            for i, ss in enumerate(sections):
                ss.set_row_index(i)
        if parent:
            break

        assert parent, "Could not find the parent sequence"

    unreal.EditorAssetLibrary.delete_asset(level_sequence.get_path_name())

    settings = unreal.MovieSceneUserImportFBXSettings()
    settings.set_editor_property('reduce_keys', False)

    tools = unreal.AssetToolsHelpers().get_asset_tools()
    new_sequence = tools.create_asset(
        asset_name=sequence_name,
        package_path=asset_dir,
        asset_class=unreal.LevelSequence,
        factory=unreal.LevelSequenceFactoryNew()
    )

    new_sequence.set_display_rate(display_rate)
    new_sequence.set_playback_start(playback_start)
    new_sequence.set_playback_end(playback_end)

    sub_scene.set_sequence(new_sequence)

    return {"return": new_sequence.get_path_name()}


def remove_camera(params):
    asset_dir, asset, root = get_params(params, 'asset_dir', 'asset', 'root')

    path = Path(asset_dir)

    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    _filter = unreal.ARFilter(
        class_names=["LevelSequence"],
        package_paths=[asset_dir],
        recursive_paths=False)
    sequences = ar.get_assets(_filter)

    if not sequences:
        raise FileNotFoundError("Could not find sequence.")

    world = ar.get_asset_by_object_path(
        unreal.EditorLevelLibrary.get_editor_world().get_path_name())

    _filter = unreal.ARFilter(
        class_names=["World"],
        package_paths=[asset_dir],
        recursive_paths=True)
    levels = ar.get_assets(_filter)

    # There should be only one map in the list
    if not levels:
        raise FileNotFoundError("Could not find map.")

    level = levels[0]

    unreal.EditorLevelLibrary.save_all_dirty_levels()
    unreal.EditorLevelLibrary.load_level(level.get_asset().get_path_name())

    # Remove the camera from the level.
    actors = unreal.EditorLevelLibrary.get_all_level_actors()

    for a in actors:
        if a.__class__ == unreal.CineCameraActor:
            unreal.EditorLevelLibrary.destroy_actor(a)

    unreal.EditorLevelLibrary.save_all_dirty_levels()
    unreal.EditorLevelLibrary.load_level(world.get_asset().get_path_name())

    # There should be only one sequence in the path.
    sequence_name = sequences[0].asset_name

    # Remove the Level Sequence from the parent.
    # We need to traverse the hierarchy from the master sequence to find
    # the level sequence.
    namespace = asset_dir.replace(f"{root}/", "")
    ms_asset = namespace.split('/')[0]
    _filter = unreal.ARFilter(
        class_names=["LevelSequence"],
        package_paths=[f"{root}/{ms_asset}"],
        recursive_paths=False)
    sequences = ar.get_assets(_filter)
    master_sequence = sequences[0].get_asset()
    _filter = unreal.ARFilter(
        class_names=["World"],
        package_paths=[f"{root}/{ms_asset}"],
        recursive_paths=False)
    levels = ar.get_assets(_filter)
    master_level = levels[0].get_full_name()

    sequences = [master_sequence]

    parent = None
    for s in sequences:
        tracks = s.get_master_tracks()
        subscene_track = None
        visibility_track = None
        for t in tracks:
            if t.get_class() == unreal.MovieSceneSubTrack.static_class():
                subscene_track = t
            if (t.get_class() ==
                    unreal.MovieSceneLevelVisibilityTrack.static_class()):
                visibility_track = t
        if subscene_track:
            sections = subscene_track.get_sections()
            for ss in sections:
                if ss.get_sequence().get_name() == sequence_name:
                    parent = s
                    subscene_track.remove_section(ss)
                    break
                sequences.append(ss.get_sequence())
            # Update subscenes indexes.
            for i, ss in enumerate(sections):
                ss.set_row_index(i)

        if visibility_track:
            sections = visibility_track.get_sections()
            for ss in sections:
                if (unreal.Name(f"{asset}_map_camera")
                        in ss.get_level_names()):
                    visibility_track.remove_section(ss)
            # Update visibility sections indexes.
            i = -1
            prev_name = []
            for ss in sections:
                if prev_name != ss.get_level_names():
                    i += 1
                ss.set_row_index(i)
                prev_name = ss.get_level_names()
        if parent:
            break

    assert parent, "Could not find the parent sequence"

    # Create a temporary level to delete the layout level.
    unreal.EditorLevelLibrary.save_all_dirty_levels()
    unreal.EditorAssetLibrary.make_directory(f"{root}/tmp")
    tmp_level = f"{root}/tmp/temp_map"
    if not unreal.EditorAssetLibrary.does_asset_exist(f"{tmp_level}.temp_map"):
        unreal.EditorLevelLibrary.new_level(tmp_level)
    else:
        unreal.EditorLevelLibrary.load_level(tmp_level)

    # Delete the layout directory.
    unreal.EditorAssetLibrary.delete_directory(asset_dir)

    unreal.EditorLevelLibrary.load_level(master_level)
    unreal.EditorAssetLibrary.delete_directory(f"{root}/tmp")

    # Check if there isn't any more assets in the parent folder, and
    # delete it if not.
    asset_content = unreal.EditorAssetLibrary.list_assets(
        path.parent.as_posix(), recursive=False, include_folder=True
    )

    if len(asset_content) == 0:
        unreal.EditorAssetLibrary.delete_directory(path.parent.as_posix())


def get_and_load_master_level(params):
    path = get_params(params, 'path')
    ar = unreal.AssetRegistryHelpers.get_asset_registry()

    _filter = unreal.ARFilter(
        class_names=["World"],
        package_paths=[path],
        recursive_paths=False)
    levels = ar.get_assets(_filter)
    master_level = levels[0].get_asset().get_path_name()

    unreal.EditorLevelLibrary.load_level(master_level)


def set_sequences_range(params):
    """
    Set range of all sections
    Changing the range of the section is not enough. We need to change
    the frame of all the keys in the section.

    Args:
        params (str): string containing a dictionary with parameters:
            sequence (str): path to the sequence

    """
    cam_seq_path, clip_in, clip_out, frame_start = get_params(
        params, 'sequence', 'clip_in', 'clip_out', 'frame_start')

    cam_seq = get_asset(cam_seq_path)

    for possessable in cam_seq.get_possessables():
        for tracks in possessable.get_tracks():
            for section in tracks.get_sections():
                section.set_range(
                    clip_in,
                    clip_out + 1)
                for channel in section.get_all_channels():
                    for key in channel.get_keys():
                        old_time = key.get_time().get_editor_property(
                            'frame_number')
                        old_time_value = old_time.get_editor_property(
                            'value')
                        new_time = old_time_value + (clip_in - frame_start)
                        key.set_time(unreal.FrameNumber(value=new_time))


def _transform_from_basis(transform, basis):
    """Transform a transform from a basis to a new basis."""
    # Get the basis matrix
    basis_matrix = unreal.Matrix(
        basis[0],
        basis[1],
        basis[2],
        basis[3]
    )
    transform_matrix = unreal.Matrix(
        transform[0],
        transform[1],
        transform[2],
        transform[3]
    )

    new_transform = (
        basis_matrix.get_inverse() * transform_matrix * basis_matrix)

    return new_transform.transform()


def process_family(params):
    """
    Args:
        params (str): string containing a dictionary with parameters:
            assets (list): list of paths to the assets
            class_name (str): name of the class to spawn
            instance_name (str): name of the instance
            transform (list): list of 4 vectors representing the transform
            basis (list): list of 4 vectors representing the basis
            sequence_path (str): path to the sequence
    """
    (assets, class_name, instance_name, transform, basis,
     sequence_path) = get_params(params, 'assets', 'class_name',
                                 'instance_name', 'transform', 'basis',
                                 'sequence_path')

    basis = eval(basis)
    transform = eval(transform)

    actors = []
    bindings = []

    sequence = get_asset(sequence_path) if sequence_path else None

    for asset in assets:
        obj = get_asset(asset)
        if obj and obj.get_class().get_name() == class_name:
            t = _transform_from_basis(transform, basis)
            actor = unreal.EditorLevelLibrary.spawn_actor_from_object(
                obj, t.translation
            )
            actor.set_actor_label(instance_name)
            actor.set_actor_rotation(t.rotation.rotator(), False)
            actor.set_actor_scale3d(t.scale3d)

            if class_name == 'SkeletalMesh':
                skm_comp = actor.get_editor_property('skeletal_mesh_component')
                skm_comp.set_bounds_scale(10.0)

            actors.append(actor.get_path_name())

            if sequence:
                binding = None
                for p in sequence.get_possessables():
                    if p.get_name() == actor.get_name():
                        binding = p
                        break

                if not binding:
                    binding = sequence.add_possessable(actor)

                bindings.append(binding.get_id().to_string())

    return {"return": (actors, bindings)}


def apply_animation_to_actor(params):
    """
    Args:
        params (str): string containing a dictionary with parameters:
            actor_path (str): path to the actor
            animation_path (str): path to the animation
    """
    actor_path, animation_path = get_params(
        params, 'actor_path', 'animation_path')

    actor = get_asset(actor_path)
    animation = get_asset(animation_path)

    animation.set_editor_property('enable_root_motion', True)

    actor.skeletal_mesh_component.set_editor_property(
        'animation_mode', unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    actor.skeletal_mesh_component.animation_data.set_editor_property(
        'anim_to_play', animation)


def apply_animation(params):
    """
    Args:
        params (str): string containing a dictionary with parameters:
            animation_path (str): path to the animation
            instance_name (str): name of the instance
            sequences (str): list of paths to the sequences
    """
    animation_path, instance_name, sequences = get_params(
        params, 'animation_path', 'instance_name', 'sequences')

    animation = get_asset(animation_path)

    anim_track_class = "MovieSceneSkeletalAnimationTrack"
    anim_section_class = "MovieSceneSkeletalAnimationSection"

    for sequence_path in sequences:
        sequence = get_asset(sequence_path)
        possessables = [
            possessable for possessable in sequence.get_possessables()
            if possessable.get_display_name() == instance_name]

        for possessable in possessables:
            tracks = [
                track for track in possessable.get_tracks()
                if (track.get_class().get_name() == anim_track_class)]

            if not tracks:
                track = possessable.add_track(
                    unreal.MovieSceneSkeletalAnimationTrack)
                tracks.append(track)

            for track in tracks:
                sections = [
                    section for section in track.get_sections()
                    if (section.get_class().get_name == anim_section_class)]

                if not sections:
                    sections.append(track.add_section())

                for section in sections:
                    section.params.set_editor_property('animation', animation)
                    section.set_range(
                        sequence.get_playback_start(),
                        sequence.get_playback_end() - 1)
                    section.set_completion_mode(
                        unreal.MovieSceneCompletionMode.KEEP_STATE)


def add_animation_to_sequencer(params):
    """
    Args:
        params (str): string containing a dictionary with parameters:
            sequence_path (str): path to the sequence
            binding_guid (str): guid of the binding
            animation_path (str): path to the animation
    """
    sequence_path, binding_guid, animation_path = get_params(
        params, 'sequence_path', 'binding_guid', 'animation_path')

    sequence = get_asset(sequence_path)
    animation = get_asset(animation_path)

    binding = next(
        (
            b
            for b in sequence.get_possessables()
            if b.get_id().to_string() == binding_guid
        ),
        None,
    )
    tracks = binding.get_tracks()
    track = tracks[0] if tracks else binding.add_track(
        unreal.MovieSceneSkeletalAnimationTrack)

    sections = track.get_sections()
    if not sections:
        section = track.add_section()
    else:
        section = sections[0]

        sec_params = section.get_editor_property('params')
        if curr_anim := sec_params.get_editor_property('animation'):
            # Checks if the animation path has a container.
            # If it does, it means that the animation is
            # already in the sequencer.
            anim_path = str(Path(
                curr_anim.get_path_name()).parent
                            ).replace('\\', '/')

            ar = unreal.AssetRegistryHelpers.get_asset_registry()

            _filter = unreal.ARFilter(
                class_names=["AyonAssetContainer"],
                package_paths=[anim_path],
                recursive_paths=False)
            containers = ar.get_assets(_filter)

            if len(containers) > 0:
                return

    section.set_range(
        sequence.get_playback_start(),
        sequence.get_playback_end())
    sec_params = section.get_editor_property('params')
    sec_params.set_editor_property('animation', animation)


def import_camera(params):
    """
    Args:
        params (str): string containing a dictionary with parameters:
            sequence_path (str): path to the sequence
            import_filename (str): path to the fbx file
    """
    sequence_path, import_filename = get_params(
        params, 'sequence_path', 'import_filename')

    sequence = get_asset(sequence_path)

    world = unreal.EditorLevelLibrary.get_editor_world()

    settings = unreal.MovieSceneUserImportFBXSettings()
    settings.set_editor_property('reduce_keys', False)

    if UNREAL_VERSION.major == 4 and UNREAL_VERSION.minor <= 26:
        unreal.SequencerTools.import_fbx(
            world,
            sequence,
            sequence.get_bindings(),
            settings,
            import_filename
        )
    elif ((UNREAL_VERSION.major == 4 and UNREAL_VERSION.minor >= 27) or
          UNREAL_VERSION.major == 5):
        unreal.SequencerTools.import_level_sequence_fbx(
            world,
            sequence,
            sequence.get_bindings(),
            settings,
            import_filename
        )
    else:
        raise NotImplementedError(
            f"Unreal version {UNREAL_VERSION.major} not supported")


def get_actor_and_skeleton(params):
    """
    Args:
        params (str): string containing a dictionary with parameters:
            instance_name (str): name of the instance
    """
    instance_name = get_params(params, 'instance_name')

    actor_subsystem = unreal.EditorActorSubsystem()
    actors = actor_subsystem.get_all_level_actors()
    actor = None
    for a in actors:
        if a.get_class().get_name() != "SkeletalMeshActor":
            continue
        if a.get_actor_label() == instance_name:
            actor = a
            break
    if not actor:
        raise RuntimeError(f"Could not find actor {instance_name}")

    skeleton = actor.skeletal_mesh_component.skeletal_mesh.skeleton

    return {"return": (actor.get_path_name(), skeleton.get_path_name())}


def get_skeleton_from_skeletal_mesh(params):
    """
    Args:
        params (str): string containing a dictionary with parameters:
            skeletal_mesh_path (str): path to the skeletal mesh
    """
    skeletal_mesh_path = get_params(params, 'skeletal_mesh_path')

    skeletal_mesh = unreal.EditorAssetLibrary.load_asset(skeletal_mesh_path)
    skeleton = skeletal_mesh.get_editor_property('skeleton')

    return {"return": skeleton.get_path_name()}


def remove_asset(params):
    """
    Args:
        params (str): string containing a dictionary with parameters:
            path (str): path to the asset
    """
    path = get_params(params, 'path')

    parent_path = Path(path).parent.as_posix()

    unreal.EditorAssetLibrary.delete_directory(path)

    asset_content = unreal.EditorAssetLibrary.list_assets(
        parent_path, recursive=False, include_folder=True
    )

    if len(asset_content) == 0:
        unreal.EditorAssetLibrary.delete_directory(parent_path)


def delete_all_bound_assets(params):
    """
    Delete from the current level all the assets that are bound to the
    level sequence.

    Args:
        params (str): string containing a dictionary with parameters:
            level_sequence_path (str): path to the level sequence
    """
    level_sequence_path = get_params(params, 'level_sequence_path')

    level_sequence = get_asset(level_sequence_path)

    # Get the actors in the level sequence.
    bound_objs = unreal.SequencerTools.get_bound_objects(
        unreal.EditorLevelLibrary.get_editor_world(),
        level_sequence,
        level_sequence.get_bindings(),
        unreal.SequencerScriptingRange(
            has_start_value=True,
            has_end_value=True,
            inclusive_start=level_sequence.get_playback_start(),
            exclusive_end=level_sequence.get_playback_end()
        )
    )

    # Delete actors from the map
    for obj in bound_objs:
        actor_path = obj.bound_objects[0].get_path_name().split(":")[-1]
        actor = unreal.EditorLevelLibrary.get_actor_reference(actor_path)
        unreal.EditorLevelLibrary.destroy_actor(actor)


def _remove_subsequences(master_sequence, asset):
    """
    Traverse hierarchy to remove subsequences.

    Args:
        master_sequence (LevelSequence): master sequence
        asset (str): asset name
    """
    sequences = [master_sequence]

    parent = None
    for sequence in sequences:
        tracks = sequence.get_master_tracks()
        subscene_track = None
        visibility_track = None
        for track in tracks:
            if track.get_class().get_name() == "MovieSceneSubTrack":
                subscene_track = track
            if (track.get_class().get_name() ==
                    "MovieSceneLevelVisibilityTrack"):
                visibility_track = track

        if subscene_track:
            sections = subscene_track.get_sections()
            for section in sections:
                if section.get_sequence().get_name() == asset:
                    parent = sequence
                    subscene_track.remove_section(section)
                    break
                sequences.append(section.get_sequence())
            # Update subscenes indexes.
            for i, section in enumerate(sections):
                section.set_row_index(i)

        if visibility_track:
            sections = visibility_track.get_sections()
            for section in sections:
                if (unreal.Name(f"{asset}_map")
                        in section.get_level_names()):
                    visibility_track.remove_section(section)
            # Update visibility sections indexes.
            i = -1
            prev_name = []
            for section in sections:
                if prev_name != section.get_level_names():
                    i += 1
                section.set_row_index(i)
                prev_name = section.get_level_names()

        if parent:
            break

    assert parent, "Could not find the parent sequence"


def _remove_sequences_in_hierarchy(asset_dir, level_sequence, asset, root):
    delete_all_bound_assets(level_sequence.get_path_name())

    # Remove the Level Sequence from the parent.
    # We need to traverse the hierarchy from the master sequence to
    # find the level sequence.
    namespace = asset_dir.replace(f"{root}/", "")
    ms_asset = namespace.split('/')[0]
    master_sequence = get_asset(_get_first_asset_of_class(
        "LevelSequence", f"{root}/{ms_asset}", False))
    master_level = _get_first_asset_of_class(
        "World", f"{root}/{ms_asset}", False)

    _remove_subsequences(master_sequence, asset)

    return master_level


def remove_layout(params):
    """
    Args:
        params (str): string containing a dictionary with parameters:
            root (str): path to the root folder
            asset (str): path to the asset
            asset_dir (str): path to the asset folder
            asset_name (str): name of the asset
            loaded_assets (str): list of loaded assets
            create_sequences (str): boolean to create sequences
    """
    (root, asset, asset_dir, asset_name, loaded_assets,
     create_sequences) = get_params(params, 'root', 'asset', 'asset_dir',
                                    'asset_name', 'loaded_assets',
                                    'create_sequences')

    path = Path(asset_dir)
    parent_path = path.parent.as_posix()

    level_sequence = get_asset(_get_first_asset_of_class(
        "LevelSequence", path.as_posix(), False))
    level = _get_first_asset_of_class("World", parent_path, True)

    unreal.EditorLevelLibrary.load_level(level)

    containers = ls()
    layout_containers = [
        c for c in containers
        if c.get('asset_name') != asset_name and c.get('family') == "layout"]

    # Check if the assets have been loaded by other layouts, and deletes
    # them if they haven't.
    for loaded_asset in eval(loaded_assets):
        layouts = [
            lc for lc in layout_containers
            if loaded_asset in lc.get('loaded_assets')]

        if not layouts:
            unreal.EditorAssetLibrary.delete_directory(
                Path(loaded_asset).parent.as_posix())

            # Delete the parent folder if there aren't any more
            # layouts in it.
            asset_content = unreal.EditorAssetLibrary.list_assets(
                Path(loaded_asset).parent.parent.as_posix(), recursive=False,
                include_folder=True
            )

            if len(asset_content) == 0:
                unreal.EditorAssetLibrary.delete_directory(
                    str(Path(loaded_asset).parent.parent))

    master_level = None

    if create_sequences:
        master_level = _remove_sequences_in_hierarchy(
            asset_dir, level_sequence, asset, root)

    actors = unreal.EditorLevelLibrary.get_all_level_actors()

    if not actors:
        # Delete the level if it's empty.
        # Create a temporary level to delete the layout level.
        unreal.EditorLevelLibrary.save_all_dirty_levels()
        unreal.EditorAssetLibrary.make_directory(f"{root}/tmp")
        tmp_level = f"{root}/tmp/temp_map"
        if not unreal.EditorAssetLibrary.does_asset_exist(
                f"{tmp_level}.temp_map"):
            unreal.EditorLevelLibrary.new_level(tmp_level)
        else:
            unreal.EditorLevelLibrary.load_level(tmp_level)

    # Delete the layout directory.
    unreal.EditorAssetLibrary.delete_directory(path.as_posix())

    if not actors:
        unreal.EditorAssetLibrary.delete_directory(path.parent.as_posix())

    if create_sequences:
        unreal.EditorLevelLibrary.load_level(master_level)
        unreal.EditorAssetLibrary.delete_directory(f"{root}/tmp")


def match_actor(params):
    """
    Match existing actors in the scene to the layout that is being loaded.
    It will create a container for each of them, and apply the transformations
    from the layout.

    Args:
        params (str): string containing a dictionary with parameters:
            actors_matched (list): list of actors already matched
            lasset (dict): dictionary containing the layout asset
            repr_data (dict): dictionary containing the representation
    """
    actors_matched, lasset, repr_data = get_params(
        params, 'actors_matched', 'lasset', 'repr_data')

    actors = unreal.EditorLevelLibrary.get_all_level_actors()

    for actor in actors:
        if actor.get_class().get_name() != 'StaticMeshActor':
            continue
        if actor in actors_matched:
            continue

        # Get the original path of the file from which the asset has
        # been imported.
        smc = actor.get_editor_property('static_mesh_component')
        mesh = smc.get_editor_property('static_mesh')
        import_data = mesh.get_editor_property('asset_import_data')
        filename = import_data.get_first_filename()
        path = Path(filename)

        if (not path.name or
                path.name not in repr_data.get('data').get('path')):
            continue

        actor.set_actor_label(lasset.get('instance_name'))

        mesh_path = Path(mesh.get_path_name()).parent.as_posix()

        # Set the transform for the actor.
        basis_data = lasset.get('basis')
        transform_data = lasset.get('transform_matrix')
        transform = _get_transform(import_data, basis_data, transform_data)

        actor.set_actor_transform(transform, False, True)

        return True, mesh_path

    return False, None


def _spawn_actor(obj, lasset):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_object(
        obj, unreal.Vector(0.0, 0.0, 0.0)
    )

    actor.set_actor_label(lasset.get('instance_name'))
    smc = actor.get_editor_property('static_mesh_component')
    mesh = smc.get_editor_property('static_mesh')
    import_data = mesh.get_editor_property('asset_import_data')

    basis_data = lasset.get('basis')
    transform_data = lasset.get('transform_matrix')
    transform = _get_transform(import_data, basis_data, transform_data)

    actor.set_actor_transform(transform, False, True)


def spawn_existing_actors(params):
    """
    Spawn actors that have already been loaded from the layout asset.

    Args:
        params (str): string containing a dictionary with parameters:
            repr_data (dict): dictionary containing the representation
            lasset (dict): dictionary containing the layout asset
    """
    repr_data, lasset = get_params(params, 'repr_data', 'lasset')

    ar = unreal.AssetRegistryHelpers.get_asset_registry()

    all_containers = ls()

    for container in all_containers:
        representation = container.get('representation')

        if representation != str(repr_data.get('_id')):
            continue

        asset_dir = container.get('namespace')

        _filter = unreal.ARFilter(
            class_names=["StaticMesh"],
            package_paths=[asset_dir],
            recursive_paths=False)
        assets = ar.get_assets(_filter)

        for asset in assets:
            obj = asset.get_asset()
            _spawn_actor(obj, lasset)

        return True

    return False


def spawn_actors(params):
    """
    Spawn actors from a list of assets.

    Args:
        params (str): string containing a dictionary with parameters:
            lasset (dict): dictionary containing the layout asset
            repr_data (dict): dictionary containing the representation
    """
    assets, lasset = get_params(params, 'assets', 'lasset')

    ar = unreal.AssetRegistryHelpers.get_asset_registry()

    for asset in assets:
        obj = ar.get_asset_by_object_path(asset).get_asset()
        if obj.get_class().get_name() != 'StaticMesh':
            continue
        _spawn_actor(obj, lasset)

    return True


def remove_unmatched_actors(params):
    """
    Remove actors that have not been matched to the layout.

    Args:
        params (str): string containing a dictionary with parameters:
            actors_matched (list): list of actors already matched
    """
    actors_matched = get_params(params, 'actors_matched')

    actors = unreal.EditorLevelLibrary.get_all_level_actors()

    for actor in actors:
        if actor.get_class().get_name() != 'StaticMeshActor':
            continue
        if actor not in actors_matched:
            unreal.log_warning(f"Actor {actor.get_name()} not matched.")
            unreal.EditorLevelLibrary.destroy_actor(actor)
