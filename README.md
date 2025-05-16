# MusicViz

MusicViz is a Python tool that generates a dynamic music visualizer video from an audio file (MP3 or WAV). It creates a video with animated frequency spectrum bars and particle effects synchronized to the audio, using a colorful plasma colormap and a black background for a vibrant visual experience. The output is an MP4 video file with the audio embedded.

## Features

- Generates a visualizer with non-overlapping frequency bars based on the audio's spectrogram.
- Adds particle effects that respond to frequency peaks for a dynamic look.
- Supports MP3 and WAV audio inputs.
- Customizable video title displayed in the output.
- Produces high-quality 1920x1080 MP4 videos at 30 FPS.
- Uses a plasma colormap for visually appealing, frequency-based coloring.

## Installation

First create a new conda environment:

```
conda create -n musicv python=3.11
```

Then activate it:

```
conda activate musicv
```

You can now install musicviz:

```
pip3 install musicviz
```

## Dependencies

### Install FFmpeg:

This tool requires FFmpeg for video encoding.

Download and install FFmpeg from ffmpeg.org or via a package manager:

On Ubuntu:

```
sudo apt-get install ffmpeg
```

On macOS: 

```
brew install ffmpeg
```

Ensure ffmpeg is available in your system PATH.

## Usage

Run the `musicviz` tool from the command line, providing the input audio file, output video file, and a title for the video.

```
musicviz <input_audio> <output_video> <video_title>
```

For example:

```
musicviz song.mp3 output.mp4 "My Awesome Track"
```

## Output

The output is a 1920x1080 MP4 video with:

- Frequency bars that pulse with the audio's amplitude.
- A black background with a plasma colormap for bars.
- The specified title displayed at the top.
- The original audio embedded in the video.



