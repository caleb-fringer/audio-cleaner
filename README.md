---
title: audio-cleaner
app_file: app.py
sdk: gradio
sdk_version: 6.27.0
---
# Audio Cleaner
This project uses [demucs](https://github.com/adefossez/demucs) to remove
background noise from vocals in video files. It can be used to clean up videos
w/ vocals that have a lot of distracting noises (for instance, Microsoft Teams
notifications).

# Usage
First, [install uv](https://docs.astral.sh/uv/#installation)

Next, from the root of this repository run `uv sync`

Then, run `uv run app.py`. This should launch a local server on
`http://localhost:8080`. Naviage to this in the browser of your choice.

Upload your videos, either by drag-and-drop or by the file browser interface.
Click "Clean", and wait for the progress to finish.

When they are finished cleaning, click the "Download" button next to the cleaned
files.

# Branding Clip
Currently, this adds a 5 second Mission College logo clip to videos, as this was
part of the use case that inspired this project. When I have more time, this
will be made optional.
