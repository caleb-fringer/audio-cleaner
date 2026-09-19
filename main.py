from pathlib import Path
import argparse

import torch
from demucs.api import Separator
from torchcodec.decoders import AudioDecoder, VideoDecoder
from torchcodec.encoders import Encoder
from torchcodec.transforms import Resize


def clean_audio(
    video_path: Path,
    separator: Separator,
    progress,
    state=None,
    audio_buffer_size=44100,
    video_buffer_size=128,
):
    video = VideoDecoder(video_path)

    video_height = video.metadata.height
    video_width = video.metadata.width
    video_fps = video.metadata.average_fps
    video_frame_count = video.metadata.num_frames

    if video_height is None or video_width is None:
        raise ValueError("Could not determine video dimensions")

    if video_fps is None:
        raise ValueError("Could not determine video frame rate")

    if video_frame_count is None:
        raise ValueError("Could not determine video frame count")

    # ------------------------------------------------------------------
    # Load branding clip
    # ------------------------------------------------------------------

    brand_clip = VideoDecoder(
        "Mission_Branding.mp4",
        transforms=[Resize((video_height, video_width))],
    )

    if brand_clip.metadata.average_fps != video_fps:
        raise ValueError(
            "Branding clip FPS does not match source video FPS"
        )

    # ------------------------------------------------------------------
    # Decode source audio
    # ------------------------------------------------------------------

    audio = AudioDecoder(
        video_path,
        num_channels=2,
    )

    audio_samples = audio.get_all_samples()

    input_sample_count = audio_samples.data.shape[-1]
    audio_duration = input_sample_count / separator.samplerate

    if state is not None:
        state["audio_duration"] = audio_duration

    # ------------------------------------------------------------------
    # Separate audio with Demucs
    # ------------------------------------------------------------------

    if progress is not None and state is not None:
        progress(
            0,
            desc=(
                f"File {state['file']} / {state['total_files']}: "
                f"{video_path.name} — Separating audio "
                f"(0.0 / {audio_duration:.1f} sec)"
            ),
        )

    file, sources = separator.separate_tensor(audio_samples.data)

    separated_vocals = sources["vocals"]

    # ------------------------------------------------------------------
    # Set up encoder
    # ------------------------------------------------------------------

    encoder = Encoder()

    audio_out = encoder.add_audio(
        sample_rate=separator.samplerate,
        num_channels=2,
    )

    video_out = encoder.add_video(
        height=video_height,
        width=video_width,
        frame_rate=video_fps,
    )

    # ------------------------------------------------------------------
    # Output path
    # ------------------------------------------------------------------

    out_path = (
        Path(video_path.parent)
        / f"{video_path.stem}_cleaned.mp4"
    )

    # ------------------------------------------------------------------
    # Encode
    # ------------------------------------------------------------------

    with encoder.open_file(out_path):

        # --------------------------------------------------------------
        # 5 seconds of silence before the cleaned audio
        # --------------------------------------------------------------

        silence_samples = 5 * separator.samplerate

        audio_out.add_samples(
            torch.zeros((2, silence_samples))
        )

        if progress is not None and state is not None:
            progress(
                0,
                desc=(
                    f"File {state['file']} / {state['total_files']}: "
                    f"{video_path.name} — Encoding audio"
                ),
            )

        # --------------------------------------------------------------
        # Branding video
        # --------------------------------------------------------------

        brand_clip_frames = brand_clip.get_all_frames(
            fps=video_fps
        )

        video_out.add_frames(
            brand_clip_frames.data
        )

        # --------------------------------------------------------------
        # Encode separated audio in chunks
        # --------------------------------------------------------------

        separated_sample_count = separated_vocals.shape[-1]

        for start in range(
            0,
            separated_sample_count,
            audio_buffer_size,
        ):
            end = min(
                start + audio_buffer_size,
                separated_sample_count,
            )

            samples = separated_vocals[:, start:end]

            audio_out.add_samples(samples)

            if progress is not None and state is not None:
                progress(
                    end / separated_sample_count,
                    desc=(
                        f"File {state['file']} / "
                        f"{state['total_files']}: "
                        f"{video_path.name} — Encoding audio "
                        f"({end / separator.samplerate:.1f} / "
                        f"{separated_sample_count / separator.samplerate:.1f} sec)"
                    ),
                )

        # --------------------------------------------------------------
        # Encode source video in chunks
        # --------------------------------------------------------------

        total_frames = video_frame_count
        encoded_frames = 0

        if progress is not None and state is not None:
            progress(
                0,
                desc=(
                    f"File {state['file']} / {state['total_files']}: "
                    f"{video_path.name} — Encoding video "
                    f"(0 / {total_frames:,} frames)"
                ),
            )

        for start in range(
            0,
            total_frames,
            video_buffer_size,
        ):
            frames = video.get_frames_in_range(
                start,
                min(start + video_buffer_size, total_frames),
            )

            video_out.add_frames(frames.data)

            encoded_frames += len(frames)

            if progress is not None and state is not None:
                progress(
                    encoded_frames / total_frames,
                    desc=(
                        f"File {state['file']} / "
                        f"{state['total_files']}: "
                        f"{video_path.name} — Encoding video "
                        f"({encoded_frames:,} / "
                        f"{total_frames:,} frames)"
                    ),
                )

    return out_path


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "videos",
        nargs="+",
        type=Path,
    )

    args = parser.parse_args()

    separator = Separator(
        model="htdemucs",
        progress=True,
    )

    for path in args.videos:
        clean_audio(
            path,
            separator,
            None,
        )


if __name__ == "__main__":
    main()
