from pathlib import Path
from typing import List

import gradio as gr
from demucs.api import Separator

from main import clean_audio


def clean_audio_wrapper(
    path_strings: List[str],
    progress=gr.Progress(),
):
    total_files = len(path_strings)

    paths = [Path(path) for path in path_strings]

    state = {
        "file": 0,
        "total_files": total_files,
        "audio_duration": 0.0,
    }

    def separation_callback(info: dict):
        if info["state"] != "end":
            return

        segment_offset = info["segment_offset"]
        audio_length = info["audio_length"]

        fraction = segment_offset / audio_length
        seconds = fraction * state["audio_duration"]

        progress(
            fraction,
            desc=(
                f"File {state['file']} / {state['total_files']}: "
                f"{state['path'].name} — Separating audio "
                f"({seconds:.1f} / "
                f"{state['audio_duration']:.1f} sec)"
            ),
        )

    separator = Separator(
        model="htdemucs",
        progress=True,
        callback=separation_callback,
    )

    result = []

    for i, path in enumerate(paths, start=1):
        state["file"] = i
        state["path"] = path

        progress(
            0,
            desc=(
                f"File {i} / {total_files}: "
                f"{path.name} — Starting"
            ),
        )

        out_path = clean_audio(
            path,
            separator,
            progress,
            state=state,
            video_buffer_size=32,
        )

        result.append(str(out_path))

    return result


video_component = gr.File(
    file_types=["video"],
    file_count="multiple",
)

demo = gr.Interface(
    fn=clean_audio_wrapper,
    inputs=video_component,
    outputs=video_component,
    flagging_mode="never",
    submit_btn="Clean",
    clear_btn="Reset"
)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    print(f"Server listening on port {port}...")
    demo.launch(server_name="0.0.0.0", server_port=port)
