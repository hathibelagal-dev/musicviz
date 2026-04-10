# 🎵 MusicViz

[![PyPI - Version](https://img.shields.io/pypi/v/musicviz)](https://pypi.org/project/musicviz/)
[![PyPI - Status](https://img.shields.io/pypi/status/musicviz)](https://pypi.org/project/musicviz/)
[![PyPI - License](https://img.shields.io/pypi/l/musicviz)](https://github.com/hathibelagal-dev/musicviz/blob/main/LICENSE)

**MusicViz** is a high-performance, aesthetically driven Python tool that transforms your audio tracks into vibrant, neon-drenched visual experiences. Powered by Pygame and Librosa, it generates 1920x1080 MP4 videos with fluid, musically-accurate frequency bars.

---

## ✨ Features

- **Neon Aesthetic**: Mirrored, centered frequency bars with soft glow effects and a reactive background that pulses with the bass.
- **Beat Explosions**: Dynamic particle bursts that trigger on every major beat for high-impact visuals.
- **Beat-Reactive Colors**: The entire color palette shifts significantly on beats, keeping the experience fresh and energetic.
- **Musically Accurate**: Uses **Mel-Spectrogram** analysis to map frequencies to a human-perceivable scale, ensuring the visuals "feel" right.
- **Fluid Motion**: Implements **Temporal Smoothing** (exponential decay) for professional, non-flickering bar movement.
- **High Performance**: Pre-calculated audio analysis and headless Pygame rendering for fast video encoding.
- **Professional Layout**: Left-aligned titles and optional artist subtitles for a clean, modern look.

## 🚀 Installation

### 1. Requirements
- **Python 3.11+**
- **FFmpeg**: Required for video encoding.
    - **macOS**: `brew install ffmpeg`
    - **Ubuntu**: `sudo apt-get install ffmpeg`

### 2. Setup
It is recommended to use a virtual environment:

```bash
conda create -n musicv python=3.11
conda activate musicv
pip install musicviz
```

For development, install from source:
```bash
git clone https://github.com/hathibelagal-dev/musicviz.git
cd musicviz
pip install .
```

## 🎨 Usage

Run the `musicviz` command providing your input audio, desired output name, and track details:

```bash
musicviz <input_audio> <output_video> "Track Title" --artist "Artist Name"
```

### Example:
```bash
musicviz song.mp3 output.mp4 "Midnight Neon" --artist "SynthWave Artist"
```

## 🎥 Output Specifications

- **Resolution**: 1920x1080 (1080p)
- **Frame Rate**: 30 FPS
- **Color Palette**: Dynamic Plasma/Neon (Blue to Pink)
- **Format**: MP4 (H.264 codec) with AAC audio

---

## 🛠️ Built With

- **[Librosa](https://librosa.org/)**: Audio and music processing.
- **[Pygame](https://www.pygame.org/)**: High-performance graphics rendering.
- **[MoviePy](https://zulko.github.io/moviepy/)**: Video editing and encoding.
- **[NumPy](https://numpy.org/)**: Heavy-duty numerical operations.
