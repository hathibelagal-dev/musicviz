import librosa
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from moviepy.editor import VideoClip, AudioFileClip
import argparse
import os
import logging

def load_audio(audio_path):
    """Load audio file and return time series and sample rate."""
    y, sr = librosa.load(audio_path)
    return y, sr

import matplotlib.cm as cm
import matplotlib.patches as patches

def generate_particles(freqs, fft, num_particles=20, max_freq=5000, width=1920):
    """Generate particle positions and sizes based on frequency peaks."""
    particles = []
    if len(fft) == 0:
        return particles
    # Select top frequencies
    idx = np.argsort(fft)[-num_particles:]
    for i in idx:
        x = freqs[i] / max_freq * width  # Scale to width
        y = np.random.uniform(0, 1080)  # Random y-position
        size = fft[i] * 20  # Size based on amplitude
        particles.append((x, y, size))
    return particles

def make_frame(t, y, sr, duration, height=1080, width=1920, movie_title=""):
    """Generate a single frame with fewer, thicker, non-overlapping bars."""
    # Set up the figure
    fig = plt.figure(figsize=(width/100, height/100), dpi=100)
    ax = fig.add_subplot(111)
    
    # Compute the spectrogram for the current time window
    sample_start = int(t * sr)
    window_size = int(0.1 * sr)  # 100ms window
    sample_end = min(sample_start + window_size, len(y))
    
    # Extract windowed audio
    y_window = y[sample_start:sample_end]
    
    # Compute FFT for the window
    fft = np.abs(np.fft.fft(y_window))
    freqs = np.fft.fftfreq(len(fft), 1/sr)
    idx = freqs > 0  # Only positive frequencies
    freqs = freqs[idx]
    fft = fft[idx]
    
    # Limit to frequencies up to 5kHz
    max_freq = 5000
    idx = freqs < max_freq
    freqs = freqs[idx]
    fft = fft[idx]
    
    # Normalize FFT
    fft = fft / (np.max(fft) + 1e-10)
    
    # Bin frequencies to reduce number of bars
    num_bins = 30  # Target number of bars
    bin_edges = np.linspace(0, max_freq, num_bins + 1)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2  # Center of each bin
    bin_amplitudes = np.zeros(num_bins)
    
    # Assign FFT values to bins
    for i, freq in enumerate(freqs):
        bin_idx = np.searchsorted(bin_edges, freq) - 1
        if 0 <= bin_idx < num_bins:
            bin_amplitudes[bin_idx] += fft[i]
    
    # Average amplitudes within bins
    bin_counts = np.histogram(freqs, bins=bin_edges, weights=np.ones_like(freqs))[0]
    bin_counts = np.maximum(bin_counts, 1)  # Avoid division by zero
    bin_amplitudes = bin_amplitudes / bin_counts
    
    # Compute energy for scaling
    energy = np.mean(bin_amplitudes)
    
    # Set black background
    ax.set_facecolor('black')
    fig.patch.set_facecolor('black')
    
    # Dynamic colors using a colormap
    cmap = cm.get_cmap('plasma')
    colors = [cmap(f / max_freq) for f in bin_centers]
    
    # Plot binned frequency spectrum with non-overlapping bars
    bar_width = (bin_edges[1] - bin_edges[0]) * 0.8  # Reduced width to prevent overlap
    for i, (freq, amp, color) in enumerate(zip(bin_centers, bin_amplitudes, colors)):
        ax.bar(freq, amp * (1 + 0.5 * energy), width=bar_width, color=color,
               edgecolor='black', alpha=0.8)
    
    # Add particle effects
    particles = generate_particles(bin_centers, bin_amplitudes, num_particles=20)
    for x, y, size in particles:
        circle = patches.Circle((x, y), size, color='white', alpha=0.5)
        ax.add_patch(circle)
    
    # Configure axes
    ax.set_xlim(0, max_freq)
    ax.set_ylim(0, 1.2)
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel('Amplitude')
    ax.set_title(movie_title, fontsize=30, color='white')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    ax.title.set_color('white')
    ax.tick_params(colors='white')
    
    # Convert plot to numpy array
    fig.canvas.draw()
    rgba_buffer = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8)
    rgba_buffer = rgba_buffer.reshape(fig.canvas.get_width_height()[::-1] + (4,))
    frame = rgba_buffer[:, :, :3]  # Drop alpha for RGB
    
    plt.close(fig)
    return frame

def create_visualizer(audio_path, output_path, movie_title):
    """Create a music visualizer video from an audio file."""
    logging.getLogger('moviepy').setLevel(logging.ERROR)
    # Load audio    
    print("Loading audio...")
    y, sr = load_audio(audio_path)
    duration = librosa.get_duration(y=y, sr=sr)
    
    # Create video clip
    print("Creating video...")
    video = VideoClip(lambda t: make_frame(t, y, sr, duration, movie_title=movie_title), duration=duration)
    
    # Load audio from the input file
    audio = AudioFileClip(audio_path)
    # Trim audio to match video duration if necessary
    audio = audio.subclip(0, duration)
    video = video.set_audio(audio)
    
    # Write to file
    print("Writing video to", output_path)
    video.write_videofile(output_path, fps=30, codec='libx264', audio_codec='aac')
    video.close()
    audio.close()

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Create a music visualizer from an audio file.")
    parser.add_argument("input", help="Path to input MP3 or WAV file")
    parser.add_argument("output", help="Path to output MP4 file")
    parser.add_argument("title", help="Title of the video")
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' does not exist.")
        return
    if not args.input.lower().endswith(('.mp3', '.wav')):
        print("Error: Input file must be an MP3 or WAV file.")
        return
    
    # Ensure output ends with .mp4
    if not args.output.lower().endswith('.mp4'):
        args.output += '.mp4'
    
    try:
        create_visualizer(args.input, args.output, args.title)
        print("Visualizer created successfully!")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()