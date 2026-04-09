import librosa
import numpy as np
import os
import argparse
import logging
from moviepy.editor import VideoClip, AudioFileClip
import pygame
import pygame.gfxdraw

# Set SDL to use dummy video driver for headless rendering
os.environ['SDL_VIDEODRIVER'] = 'dummy'

def load_and_process_audio(audio_path, fps=30):
    """Load audio and pre-calculate Mel-spectrogram."""
    print("Loading audio and analyzing frequencies...")
    # Load with librosa
    y, sr = librosa.load(audio_path)
    duration = librosa.get_duration(y=y, sr=sr)
    
    # Calculate Mel-spectrogram
    # n_mels=80 for a nice dense set of bars
    hop_length = int(sr / fps)
    S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=80, hop_length=hop_length, fmin=20, fmax=8000)
    
    # Convert to log scale (dB)
    S_db = librosa.power_to_db(S, ref=np.max)
    
    # Normalize to [0, 1] range
    # We use a fixed range for dB to ensure consistency across different tracks
    min_db = -60
    S_db = np.clip((S_db - min_db) / (-min_db), 0, 1)
    
    return y, sr, duration, S_db

class NeonVisualizer:
    def __init__(self, width=1920, height=1080, title="MusicViz"):
        pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()
            
        self.width = width
        self.height = height
        self.title = title
        self.surface = pygame.Surface((width, height))
        self.prev_bins = None
        self.decay = 0.88 # Smoothing factor for falling bars
        
        # Try to load a font
        try:
            self.font = pygame.font.SysFont("Arial", 60, bold=True)
        except:
            self.font = pygame.font.Font(None, 80)
            
    def render_frame(self, t, spectrogram, fps):
        # Get the corresponding column from spectrogram
        frame_idx = int(t * fps)
        if frame_idx >= spectrogram.shape[1]:
            frame_idx = spectrogram.shape[1] - 1
            
        current_bins = spectrogram[:, frame_idx]
        
        # Apply temporal smoothing (decay)
        if self.prev_bins is None:
            self.prev_bins = current_bins
        else:
            # Bars fall slowly but rise instantly
            current_bins = np.maximum(current_bins, self.prev_bins * self.decay)
            self.prev_bins = current_bins
            
        # 1. Draw Background
        # Subtly pulse background with bass (first few bins)
        bass_val = np.mean(current_bins[:4])
        bg_color = (int(10 + 15 * bass_val), int(10 + 10 * bass_val), int(20 + 20 * bass_val))
        self.surface.fill(bg_color)
        
        # 2. Draw Title
        title_surf = self.font.render(self.title, True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(self.width // 2, 100))
        # Draw a soft glow behind title
        for offset in range(5, 0, -1):
            glow_alpha = 50 // offset
            s = self.font.render(self.title, True, (100, 100, 255))
            s.set_alpha(glow_alpha)
            self.surface.blit(s, title_rect.move(0, 0).inflate(offset*2, offset*2))
        self.surface.blit(title_surf, title_rect)
        
        # 3. Draw Bars (Mirrored Centered)
        num_mels = len(current_bins)
        # We'll mirror them: [low ... high | high ... low] or just [low ... high] mirrored
        # Let's do a classic mirrored center: Low frequencies in middle, highs on sides
        # Or more standard: Lows on left/right, highs in middle? 
        # Actually, let's do mirrored: [High...Low | Low...High]
        
        full_bins = np.concatenate([current_bins[::-1], current_bins])
        num_total_bars = len(full_bins)
        
        bar_width = (self.width - 200) // num_total_bars
        total_w = num_total_bars * bar_width
        start_x = (self.width - total_w) // 2
        center_y = self.height // 2 + 50
        
        for i, val in enumerate(full_bins):
            # Calculate height
            h = int(val * (self.height * 0.4))
            if h < 4: h = 4
            
            # Color: Map index to a neon palette
            # Use HSV for vibrant colors
            # i ranges from 0 to num_total_bars
            # We want symmetrical colors too
            color_idx = abs(i - num_total_bars // 2) / (num_total_bars // 2)
            hue = 200 + color_idx * 100 # Blue to Purple/Pink range
            color = pygame.Color(0)
            color.hsva = (hue % 360, 90, 100, 100)
            
            x = start_x + i * bar_width
            
            # Draw top bar
            rect_top = pygame.Rect(x + 2, center_y - h, bar_width - 4, h)
            # Draw bottom bar (mirror)
            rect_bottom = pygame.Rect(x + 2, center_y, bar_width - 4, h)
            
            # Draw glow
            glow_surf = pygame.Surface((bar_width + 12, h + 12), pygame.SRCALPHA)
            glow_color = pygame.Color(0)
            glow_color.hsva = (hue % 360, 90, 100, 40) # Lower alpha for glow
            pygame.draw.rect(glow_surf, glow_color, (0, 0, bar_width + 12, h + 12), border_radius=4)
            
            # Blit glow with additive blending if possible, or just normal alpha
            self.surface.blit(glow_surf, (x - 6, center_y - h - 6))
            self.surface.blit(glow_surf, (x - 6, center_y - 6))
            
            # Draw main bars
            pygame.draw.rect(self.surface, color, rect_top, border_radius=2)
            pygame.draw.rect(self.surface, color, rect_bottom, border_radius=2)
            
            # Add a white "tip" for extra flare
            tip_h = max(2, h // 10)
            pygame.draw.rect(self.surface, (255, 255, 255), (x + 2, center_y - h, bar_width - 4, tip_h), border_radius=1)
            pygame.draw.rect(self.surface, (255, 255, 255), (x + 2, center_y + h - tip_h, bar_width - 4, tip_h), border_radius=1)
            
        # Return as RGB array (MoviePy expects H, W, 3)
        return pygame.surfarray.array3d(self.surface).swapaxes(0, 1)

def create_visualizer(audio_path, output_path, movie_title):
    """Create an enhanced music visualizer video from an audio file."""
    logging.getLogger('moviepy').setLevel(logging.ERROR)
    
    fps = 30
    y, sr, duration, spectrogram = load_and_process_audio(audio_path, fps=fps)
    
    viz = NeonVisualizer(title=movie_title)
    
    def make_frame(t):
        return viz.render_frame(t, spectrogram, fps)
    
    print("Generating video frames and encoding...")
    video = VideoClip(make_frame, duration=duration)
    
    # Load audio
    audio = AudioFileClip(audio_path)
    audio = audio.subclip(0, duration)
    video = video.set_audio(audio)
    
    print(f"Writing video to: {output_path}")
    video.write_videofile(output_path, fps=fps, codec='libx264', audio_codec='aac', threads=4)
    
    video.close()
    audio.close()
    pygame.quit()

def main():
    parser = argparse.ArgumentParser(description="Create an enhanced neon music visualizer.")
    parser.add_argument("input", help="Path to input MP3 or WAV file")
    parser.add_argument("output", help="Path to output MP4 file")
    parser.add_argument("title", help="Title of the video")
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' does not exist.")
        return
    
    if not args.input.lower().endswith(('.mp3', '.wav')):
        print("Error: Input file must be an MP3 or WAV file.")
        return
    
    if not args.output.lower().endswith('.mp4'):
        args.output += '.mp4'
    
    try:
        create_visualizer(args.input, args.output, args.title)
        print("\nSuccess! Visualizer created successfully.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
