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
    """Load audio and pre-calculate Mel-spectrogram and beats."""
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
    min_db = -60
    S_db = np.clip((S_db - min_db) / (-min_db), 0, 1)
    S_db = np.nan_to_num(S_db)
    
    # Simple beat detection
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
    # Match length to spectrogram
    if len(onset_env) > S_db.shape[1]:
        onset_env = onset_env[:S_db.shape[1]]
    elif len(onset_env) < S_db.shape[1]:
        onset_env = np.pad(onset_env, (0, S_db.shape[1] - len(onset_env)))
        
    # Detect sharp increases in energy
    energy_diff = np.diff(onset_env, prepend=0)
    beat_threshold = np.mean(energy_diff) + 2.0 * np.std(energy_diff)
    beats = energy_diff > beat_threshold
    
    return y, sr, duration, S_db, beats

class NeonVisualizer:
    def __init__(self, width=1920, height=1080, title="MusicViz", artist=None, style="bars"):
        pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()
            
        self.width = width
        self.height = height
        self.title = title
        self.artist = artist
        self.style = style # "bars", "circular", or "waveform"
        self.surface = pygame.Surface((width, height))
        self.prev_bins = None
        self.decay = 0.88 # Smoothing factor for falling bars
        self.base_hue = 200 # Initial hue (Blue)
        self.particles = [] # List for beat explosions
        
        # Try to load fonts
        try:
            self.font = pygame.font.SysFont("Arial", 40, bold=True)
            self.subtitle_font = pygame.font.SysFont("Arial", 24, italic=True)
        except:
            self.font = pygame.font.Font(None, 60)
            self.subtitle_font = pygame.font.Font(None, 36)
            
    def spawn_particles(self, hue):
        # Spawn a burst of particles centered horizontally (or from center if circular)
        count = 30
        spawn_x = self.width // 2
        spawn_y = self.height // 2
        
        if self.style == "bars" or self.style == "waveform":
            spawn_y += 50

        for _ in range(count):
            p = {
                'x': np.random.randint(0, self.width) if self.style != "circular" else spawn_x,
                'y': spawn_y,
                'vx': np.random.uniform(-5, 5),
                'vy': np.random.uniform(-8, 8),
                'life': 1.0, # 100% life
                'size': np.random.randint(4, 10),
                'color': hue
            }
            self.particles.append(p)

    def render_frame(self, t, spectrogram, beats, fps):
        # Get the corresponding column from spectrogram
        frame_idx = int(t * fps)
        if frame_idx >= spectrogram.shape[1]:
            frame_idx = spectrogram.shape[1] - 1
            
        current_bins = spectrogram[:, frame_idx]
        is_beat = beats[frame_idx]
        
        # Shift colors on beats
        if is_beat:
            self.base_hue = (self.base_hue + 60) % 360
            self.spawn_particles(self.base_hue)
            
        # Apply temporal smoothing (decay)
        if self.prev_bins is None:
            self.prev_bins = current_bins
        else:
            # Bars fall slowly but rise instantly
            current_bins = np.maximum(current_bins, self.prev_bins * self.decay)
            self.prev_bins = current_bins
            
        # 1. Draw Background
        bass_val = np.mean(current_bins[:4])
        bg_flash = 20 if is_beat else 0
        bg_color = (
            int(np.clip(10 + 15 * bass_val + bg_flash, 0, 255)), 
            int(np.clip(10 + 10 * bass_val + bg_flash, 0, 255)), 
            int(np.clip(20 + 20 * bass_val + bg_flash, 0, 255))
        )
        self.surface.fill(bg_color)
        
        # 2. Draw Title and Artist (Top Left)
        margin_left = 100
        title_surf = self.font.render(self.title, True, (255, 255, 255))
        title_rect = title_surf.get_rect(topleft=(margin_left, 60))
        glow_color = pygame.Color(0)
        glow_color.hsva = (self.base_hue, 80, 100, 100)
        
        for offset in range(5, 0, -1):
            glow_alpha = 50 // offset
            s = self.font.render(self.title, True, glow_color)
            s.set_alpha(glow_alpha)
            self.surface.blit(s, title_rect.move(0, 0).inflate(offset*2, offset*2))
        self.surface.blit(title_surf, title_rect)

        if self.artist:
            artist_surf = self.subtitle_font.render(self.artist, True, (200, 200, 255))
            artist_rect = artist_surf.get_rect(topleft=(margin_left, 110))
            self.surface.blit(artist_surf, artist_rect)
        
        # Update and Draw Particles
        new_particles = []
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= 0.04 # Fade out
            if p['life'] > 0:
                p_color = pygame.Color(0)
                p_color.hsva = (p['color'], 90, 100, int(p['life'] * 100))
                pygame.draw.circle(self.surface, p_color, (int(p['x']), int(p['y'])), int(p['size']))
                new_particles.append(p)
        self.particles = new_particles
        
        # 3. Draw Visualization
        full_bins = np.concatenate([current_bins[::-1], current_bins])
        num_total_bars = len(full_bins)
        
        if self.style == "circular":
            # Circular layout
            center_x, center_y = self.width // 2, self.height // 2
            inner_radius = 150 + int(bass_val * 40) # Pulse the inner circle with bass
            max_height = self.height * 0.4
            
            # Draw a soft glow for the center
            center_glow = pygame.Surface((inner_radius*2 + 40, inner_radius*2 + 40), pygame.SRCALPHA)
            pygame.draw.circle(center_glow, (*glow_color[:3], 40), (inner_radius + 20, inner_radius + 20), inner_radius + 15)
            self.surface.blit(center_glow, (center_x - inner_radius - 20, center_y - inner_radius - 20))

            for i, val in enumerate(full_bins):
                angle = (i / num_total_bars) * (2 * np.pi)
                h = int(val * max_height)
                if h < 4: h = 4
                
                color_idx = abs(i - num_total_bars // 2) / (num_total_bars // 2)
                hue = (self.base_hue + color_idx * 60) % 360
                color = pygame.Color(0)
                color.hsva = (hue, 90, 100, 100)
                
                sin_a, cos_a = np.sin(angle), np.cos(angle)
                start_r = inner_radius
                end_r = inner_radius + h
                
                p1 = (int(center_x + start_r * cos_a), int(center_y + start_r * sin_a))
                p2 = (int(center_x + end_r * cos_a), int(center_y + end_r * sin_a))
                
                pygame.draw.line(self.surface, color, p1, p2, width=max(2, self.width // num_total_bars))
                tip_p1 = (int(center_x + (end_r - 4) * cos_a), int(center_y + (end_r - 4) * sin_a))
                pygame.draw.line(self.surface, (255, 255, 255), tip_p1, p2, width=max(2, self.width // num_total_bars))

        elif self.style == "waveform":
            # Waveform style
            center_y = self.height // 2 + 50
            margin_x = 100
            draw_width = self.width - 2 * margin_x
            
            points_top = []
            points_bottom = []
            
            for i, val in enumerate(full_bins):
                x = margin_x + (i / (num_total_bars - 1)) * draw_width
                h = val * (self.height * 0.35)
                points_top.append((x, center_y - h))
                points_bottom.append((x, center_y + h))
            
            # Draw glow and then lines
            for i in range(len(points_top) - 1):
                color_idx = abs(i - num_total_bars // 2) / (num_total_bars // 2)
                hue = (self.base_hue + color_idx * 60) % 360
                
                # Glow (using circles at points or lines with transparency)
                for w in range(10, 1, -2):
                    c = pygame.Color(0)
                    c.hsva = (hue, 90, 100, 40 // (w // 2))
                    # Cast to int for pygame.draw.line
                    p1 = (int(points_top[i][0]), int(points_top[i][1]))
                    p2 = (int(points_top[i+1][0]), int(points_top[i+1][1]))
                    p3 = (int(points_bottom[i][0]), int(points_bottom[i][1]))
                    p4 = (int(points_bottom[i+1][0]), int(points_bottom[i+1][1]))
                    pygame.draw.line(self.surface, c, p1, p2, width=w)
                    pygame.draw.line(self.surface, c, p3, p4, width=w)
                
                # Main lines
                c = pygame.Color(0)
                c.hsva = (hue, 90, 100, 100)
                pygame.draw.aaline(self.surface, c, points_top[i], points_top[i+1])
                pygame.draw.aaline(self.surface, c, points_bottom[i], points_bottom[i+1])
                
                # White core
                pygame.draw.aaline(self.surface, (255, 255, 255), (points_top[i][0], points_top[i][1]+1), (points_top[i+1][0], points_top[i+1][1]+1))
                pygame.draw.aaline(self.surface, (255, 255, 255), (points_bottom[i][0], points_bottom[i][1]-1), (points_bottom[i+1][0], points_bottom[i+1][1]-1))

        else:
            # Standard Linear layout (bars)
            bar_width = self.width // num_total_bars
            total_w = num_total_bars * bar_width
            start_x = (self.width - total_w) // 2
            center_y = self.height // 2 + 50
            
            for i, val in enumerate(full_bins):
                h = int(val * (self.height * 0.4))
                if h < 4: h = 4
                
                color_idx = abs(i - num_total_bars // 2) / (num_total_bars // 2)
                hue = (self.base_hue + color_idx * 60) % 360
                color = pygame.Color(0)
                color.hsva = (hue, 90, 100, 100)
                
                x = start_x + i * bar_width
                rect_top = pygame.Rect(x + 2, center_y - h, bar_width - 4, h)
                rect_bottom = pygame.Rect(x + 2, center_y, bar_width - 4, h)
                
                glow_surf = pygame.Surface((bar_width + 12, h + 12), pygame.SRCALPHA)
                glow_c = pygame.Color(0)
                glow_c.hsva = (hue, 90, 100, 40)
                pygame.draw.rect(glow_surf, glow_c, (0, 0, bar_width + 12, h + 12), border_radius=4)
                
                self.surface.blit(glow_surf, (x - 6, center_y - h - 6))
                self.surface.blit(glow_surf, (x - 6, center_y - 6))
                
                pygame.draw.rect(self.surface, color, rect_top, border_radius=2)
                pygame.draw.rect(self.surface, color, rect_bottom, border_radius=2)
                
                tip_h = max(2, h // 10)
                pygame.draw.rect(self.surface, (255, 255, 255), (x + 2, center_y - h, bar_width - 4, tip_h), border_radius=1)
                pygame.draw.rect(self.surface, (255, 255, 255), (x + 2, center_y + h - tip_h, bar_width - 4, tip_h), border_radius=1)
            
        return pygame.surfarray.array3d(self.surface).swapaxes(0, 1)

def create_visualizer(audio_path, output_path, movie_title, artist=None, style="bars"):
    """Create an enhanced music visualizer video from an audio file."""
    logging.getLogger('moviepy').setLevel(logging.ERROR)
    
    fps = 30
    y, sr, duration, spectrogram, beats = load_and_process_audio(audio_path, fps=fps)
    
    viz = NeonVisualizer(title=movie_title, artist=artist, style=style)
    
    def make_frame(t):
        return viz.render_frame(t, spectrogram, beats, fps)
    
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
    parser.add_argument("--artist", help="Name of the artist (optional subtitle)", default=None)
    parser.add_argument("--circular", action="store_true", help="Use a circular visualizer design")
    parser.add_argument("--waveform", action="store_true", help="Use a minimalist waveform string design")
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' does not exist.")
        return
    
    if not args.input.lower().endswith(('.mp3', '.wav')):
        print("Error: Input file must be an MP3 or WAV file.")
        return
    
    if not args.output.lower().endswith('.mp4'):
        args.output += '.mp4'
    
    style = "bars"
    if args.circular:
        style = "circular"
    elif args.waveform:
        style = "waveform"
    
    try:
        create_visualizer(args.input, args.output, args.title, artist=args.artist, style=style)
        print("\nSuccess! Visualizer created successfully.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
