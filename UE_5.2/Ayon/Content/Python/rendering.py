import os

import unreal

from helpers import (
    get_params,
    get_subsequences,
    cast_map_to_str_dict
)

queue = None
executor = None


def _queue_finish_callback(exec, success):
    unreal.log(f"Render completed. Success: {str(success)}")

    # Delete our reference so we don't keep it alive.
    global executor
    global queue
    del executor
    del queue


def _job_finish_callback(job, success):
    # You can make any edits you want to the editor world here, and the world
    # will be duplicated when the next render happens. Make sure you undo your
    # edits in OnQueueFinishedCallback if you don't want to leak state changes
    # into the editor world.
    unreal.log("Individual job completed.")


def _parse_container(container):
    """To get data from container, AssetContainer must be loaded."""

    asset = unreal.EditorAssetLibrary.load_asset(container)
    data = unreal.EditorAssetLibrary.get_metadata_tag_values(asset)
    data["objectName"] = asset.get_name()
    return cast_map_to_str_dict(data)


def _process_render_instance(instance):
    ar = unreal.AssetRegistryHelpers.get_asset_registry()

    sequence_path = instance["sequence"]
    sequence = ar.get_asset_by_object_path(sequence_path).get_asset()

    sequences = [{
        "sequence": sequence,
        "output": f"{instance['output']}",
        "frame_range": (
            int(float(instance["frameStart"])),
            int(float(instance["frameEnd"])) + 1)
    }]
    render_list = []

    # Get all the sequences to render. If there are subsequences,
    # add them and their frame ranges to the render list. We also
    # use the names for the output paths.
    for seq in sequences:
        subscenes = get_subsequences(seq.get('sequence'))

        if subscenes:
            sequences.extend(
                {
                    "sequence": sub_seq.get_sequence(),
                    "output": (
                        f"{seq.get('output')}/"
                        f"{sub_seq.get_sequence().get_name()}"
                    ),
                    "frame_range": (
                        sub_seq.get_start_frame(),
                        sub_seq.get_end_frame(),
                    ),
                }
                for sub_seq in subscenes
            )
        elif "_camera" not in seq.get('sequence').get_name():
            render_list.append(seq)

    return render_list


def _create_render_job(render, instance, config, render_dir, render_format):
    global queue

    job = queue.allocate_new_job(unreal.MoviePipelineExecutorJob)
    job.sequence = unreal.SoftObjectPath(instance["master_sequence"])
    job.map = unreal.SoftObjectPath(instance["master_level"])
    job.author = "Ayon"

    # If we have a saved configuration, copy it to the job.
    if config:
        job.get_configuration().copy_from(config)

    # User data could be used to pass data to the job, that can be
    # read in the job's OnJobFinished callback. We could,
    # for instance, pass the AyonPublishInstance's path to the job.
    # job.user_data = ""

    output_dir = render.get('output')
    shot_name = render.get('sequence').get_name()

    settings = job.get_configuration().find_or_add_setting_by_class(
        unreal.MoviePipelineOutputSetting)
    settings.output_resolution = unreal.IntPoint(1920, 1080)
    settings.custom_start_frame = render.get("frame_range")[0]
    settings.custom_end_frame = render.get("frame_range")[1]
    settings.use_custom_playback_range = True
    settings.file_name_format = f"{shot_name}" + ".{frame_number}"
    settings.output_directory.path = f"{render_dir}/{output_dir}"

    job.get_configuration().find_or_add_setting_by_class(
        unreal.MoviePipelineDeferredPassBase)

    if render_format == "png":
        job.get_configuration().find_or_add_setting_by_class(
            unreal.MoviePipelineImageSequenceOutput_PNG)
    elif render_format == "exr":
        job.get_configuration().find_or_add_setting_by_class(
            unreal.MoviePipelineImageSequenceOutput_EXR)
    elif render_format == "jpg":
        job.get_configuration().find_or_add_setting_by_class(
            unreal.MoviePipelineImageSequenceOutput_JPG)
    elif render_format == "bmp":
        job.get_configuration().find_or_add_setting_by_class(
            unreal.MoviePipelineImageSequenceOutput_BMP)
        

def _execute_render_jobs(preroll_frames):
    global executor
    executor = unreal.MoviePipelinePIEExecutor()

    settings = unreal.MoviePipelinePIEExecutorSettings()
    settings.set_editor_property(
        "initial_delay_frame_count", preroll_frames)

    executor.on_executor_finished_delegate.add_callable_unique(
        _queue_finish_callback)
    executor.on_individual_job_finished_delegate.add_callable_unique(
        _job_finish_callback)  # Only available on PIE Executor
    executor.execute(queue)


def start_rendering(params):
    """
    Start the rendering process.

    Args:
        params (dict): Dictionary with the following keys:
            - selection (list): List of selected assets.
    """
    (selection, render_dir, config_path, render_format,
     preroll_frames) = get_params(
        params, "selection", "render_dir", "config_path", "render_format",
        "preroll_frames")

    ar = unreal.AssetRegistryHelpers.get_asset_registry()

    instances = []

    for asset_path in selection:
        asset = ar.get_asset_by_object_path(asset_path).get_asset()
        if asset.get_class().get_name() == "AyonPublishInstance":
            instances.append(asset)

    render_instances = []

    for instance in instances:
        data = _parse_container(instance.get_path_name())
        if data["family"] == "render":
            render_instances.append(data)

    global queue
    queue = unreal.MoviePipelineQueue()

    if config_path and unreal.EditorAssetLibrary.does_asset_exist(config_path):
        unreal.log("Found saved render configuration")
        config = ar.get_asset_by_object_path(config_path).get_asset()

    for instance in render_instances:
        render_list = _process_render_instance(
            instance, config, render_dir, render_format)

        # Create the rendering jobs and add them to the queue.
        for render in render_list:
            _create_render_job(
                render, instance, config, render_dir, render_format)

    # If there are jobs in the queue, start the rendering process.
    if queue.get_jobs():
        _execute_render_jobs(preroll_frames)
