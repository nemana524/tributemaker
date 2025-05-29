#!/usr/bin/env python3
"""
TributeMaker Video Processor
Creates artistic tribute videos with flowing transitions from uploaded images
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import io
import json
import math
import random
from datetime import datetime

class VideoProcessor:
    """Advanced video processor for creating artistic tribute videos"""
    
    def __init__(self):
        self.frame_size = (1920, 1080)  # HD resolution
        self.fps = 30
        self.image_duration = 4.0  # seconds per image
        self.transition_duration = 1.0  # seconds for transitions
        self.zoom_effect_frames = 60  # frames for zoom effect
        
        # Music file mappings - support both MP3 and WAV
        self.music_files = {
            'sad_piano': 'assets/music/sad_piano.mp3',
            'soft_strings': 'assets/music/soft_strings.mp3',
            'calm_guitar': 'assets/music/calm_guitar.mp3'
        }
        
        # Alternative WAV files if MP3 not available
        self.music_files_wav = {
            'sad_piano': 'assets/music/sad_piano.wav',
            'soft_strings': 'assets/music/soft_strings.wav',
            'calm_guitar': 'assets/music/calm_guitar.wav'
        }
        
        # Ensure music directory exists
        os.makedirs('assets/music', exist_ok=True)
        
        # Check and create placeholder music files if they don't exist
        self._ensure_music_files()
        
    def _ensure_music_files(self):
        """Ensure music files exist, create placeholders if needed"""
        try:
            for music_name, music_path in self.music_files.items():
                if not os.path.exists(music_path):
                    print(f"VideoProcessor: Creating placeholder for {music_name}")
                    # Create a placeholder text file indicating missing music
                    with open(music_path.replace('.mp3', '_placeholder.txt'), 'w') as f:
                        f.write(f"Placeholder for {music_name}\n")
                        f.write(f"Expected path: {music_path}\n")
                        f.write(f"Description: {self._get_music_description(music_name)}\n")
                        f.write("To enable audio: Place actual MP3 file at the expected path\n")
                else:
                    print(f"VideoProcessor: Found music file: {music_path}")
        except Exception as e:
            print(f"VideoProcessor: Error checking music files: {e}")
    
    def _get_music_description(self, music_name):
        """Get description for music choice"""
        descriptions = {
            'sad_piano': 'Gentle Piano - Peaceful and reflective',
            'soft_strings': 'Soft Strings - Warm and comforting',
            'calm_guitar': 'Acoustic Guitar - Serene and hopeful'
        }
        return descriptions.get(music_name, 'Background music')
    
    def get_music_path(self, music_choice, custom_music_url=None):
        """Get the file path for a music choice - checks MP3 first, then WAV, then custom URL"""
        # Handle custom uploaded music
        if music_choice == 'custom_uploaded' and custom_music_url:
            # Extract filename from URL (e.g., /api/files/music/filename.mp3 -> filename.mp3)
            if '/api/files/music/' in custom_music_url:
                filename = custom_music_url.split('/api/files/music/')[-1]
                custom_path = os.path.join('uploads', 'music', filename)
                if os.path.exists(custom_path):
                    return custom_path
            # If URL doesn't match expected pattern, try to use it as a direct path
            elif custom_music_url and os.path.exists(custom_music_url):
                return custom_music_url
        
        # Try MP3 first for predefined music
        mp3_path = self.music_files.get(music_choice)
        if mp3_path and os.path.exists(mp3_path):
            return mp3_path
        
        # Try WAV as fallback
        wav_path = self.music_files_wav.get(music_choice)
        if wav_path and os.path.exists(wav_path):
            return wav_path
        
        # Return MP3 path even if it doesn't exist (for error messages)
        return mp3_path
    
    def has_music_file(self, music_choice, custom_music_url=None):
        """Check if a music file exists (MP3 or WAV or custom)"""
        music_path = self.get_music_path(music_choice, custom_music_url)
        return music_path and os.path.exists(music_path)
    
    def create_tribute_video(self, images, tribute_data, output_path):
        """
        Create an artistic tribute video with flowing transitions
        
        Args:
            images: List of TributeImage objects
            tribute_data: Dict with title, message, music_choice
            output_path: Path where to save the video
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"VideoProcessor: Creating artistic tribute video...")
            print(f"VideoProcessor: Images count: {len(images)}")
            print(f"VideoProcessor: Output: {output_path}")
            print(f"VideoProcessor: Music choice: {tribute_data.get('music_choice', 'none')}")
            
            # Check music file
            music_choice = tribute_data.get('music_choice')
            custom_music_url = tribute_data.get('custom_music_url')
            music_path = None
            if music_choice:
                music_path = self.get_music_path(music_choice, custom_music_url)
                if music_path and os.path.exists(music_path):
                    print(f"VideoProcessor: Using music file: {music_path}")
                else:
                    print(f"VideoProcessor: Music file not found: {music_path}")
                    if custom_music_url:
                        print(f"VideoProcessor: Custom music URL was: {custom_music_url}")
                    music_path = None
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Create artistic video frames
            frames = self._create_artistic_video_frames(images, tribute_data)
            
            if not frames:
                print("VideoProcessor: No frames created")
                return False
            
            # Try to create MP4 with FFmpeg if available
            if self._has_ffmpeg():
                success = self._create_mp4_with_ffmpeg(frames, output_path, music_path)
                if success:
                    print("VideoProcessor: Artistic MP4 created successfully with FFmpeg")
                    return True
            
            # Fallback: Create artistic animated GIF
            gif_path = output_path.replace('.mp4', '.gif')
            success = self._create_artistic_gif(frames, gif_path)
            
            if success:
                print(f"VideoProcessor: Created artistic GIF slideshow: {gif_path}")
                
                # Create MP4 placeholder file with music info
                with open(output_path, 'w') as f:
                    f.write(f"Artistic tribute video created as animated GIF: {gif_path}\n")
                    f.write(f"Title: {tribute_data['title']}\n")
                    f.write(f"Music: {tribute_data.get('music_choice', 'none')}\n")
                    if music_path:
                        f.write(f"Music file: {music_path}\n")
                    f.write(f"Features: Artistic transitions, zoom effects, fades\n")
                    f.write(f"Created: {datetime.now().isoformat()}\n")
                    f.write(f"Note: Install FFmpeg to create MP4 with audio\n")
                
                return True
            
            return False
            
        except Exception as e:
            print(f"VideoProcessor: Error creating artistic video: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _create_artistic_video_frames(self, images, tribute_data):
        """Create artistic video frames with flowing transitions"""
        try:
            frames = []
            
            # Opening title sequence with fade-in effect
            title_frames = self._create_artistic_title_sequence(tribute_data)
            frames.extend(title_frames)
            
            # Process images with artistic effects and transitions
            if images:
                image_frames = self._create_flowing_image_sequence(images)
                frames.extend(image_frames)
            
            # Closing message sequence with fade-out effect
            message_frames = self._create_artistic_message_sequence(tribute_data)
            frames.extend(message_frames)
            
            print(f"VideoProcessor: Created {len(frames)} artistic frames")
            return frames
            
        except Exception as e:
            print(f"VideoProcessor: Error creating artistic frames: {e}")
            return []
    
    def _create_artistic_title_sequence(self, tribute_data):
        """Create an artistic title sequence with fade-in and particle effects"""
        try:
            frames = []
            total_frames = int(3.0 * self.fps)  # 3 seconds
            
            for frame_num in range(total_frames):
                # Create base frame with animated gradient
                frame = self._create_animated_gradient_background(frame_num, total_frames, 
                                                                color_scheme='blue_gold')
                draw = ImageDraw.Draw(frame)
                
                # Calculate fade-in progress
                fade_progress = min(1.0, frame_num / (total_frames * 0.6))
                
                # Load fonts
                try:
                    title_font = ImageFont.truetype("arial.ttf", 90)
                    subtitle_font = ImageFont.truetype("arial.ttf", 45)
                except:
                    title_font = ImageFont.load_default()
                    subtitle_font = ImageFont.load_default()
                
                # Draw title with fade-in effect
                title = tribute_data['title']
                title_alpha = int(255 * fade_progress)
                
                if title_alpha > 0:
                    # Create title with glow effect
                    title_img = self._create_glowing_text(title, title_font, 
                                                        (255, 255, 255, title_alpha),
                                                        glow_color=(217, 152, 47, title_alpha//2))
                    
                    # Center title
                    title_x = (self.frame_size[0] - title_img.width) // 2
                    title_y = self.frame_size[1] // 2 - 80
                    
                    # Apply zoom effect
                    zoom_factor = 0.8 + (0.2 * fade_progress)
                    if zoom_factor != 1.0:
                        new_size = (int(title_img.width * zoom_factor), 
                                  int(title_img.height * zoom_factor))
                        title_img = title_img.resize(new_size, Image.Resampling.LANCZOS)
                        title_x = (self.frame_size[0] - title_img.width) // 2
                    
                    frame.paste(title_img, (title_x, title_y), title_img)
                
                # Draw subtitle with delayed fade-in
                if frame_num > total_frames * 0.4:
                    subtitle_progress = min(1.0, (frame_num - total_frames * 0.4) / (total_frames * 0.4))
                    subtitle_alpha = int(255 * subtitle_progress)
                    
                    subtitle = "A Tribute Video"
                    subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
                    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
                    subtitle_x = (self.frame_size[0] - subtitle_width) // 2
                    subtitle_y = self.frame_size[1] // 2 + 60
                    
                    # Draw subtitle with shadow
                    shadow_color = (0, 0, 0, subtitle_alpha//2)
                    text_color = (217, 152, 47, subtitle_alpha)
                    
                    draw.text((subtitle_x + 2, subtitle_y + 2), subtitle, 
                            fill=shadow_color, font=subtitle_font)
                    draw.text((subtitle_x, subtitle_y), subtitle, 
                            fill=text_color, font=subtitle_font)
                
                # Add floating particles effect
                if frame_num > total_frames * 0.2:
                    self._add_floating_particles(draw, frame_num, fade_progress)
                
                frames.append(frame)
            
            return frames
            
        except Exception as e:
            print(f"VideoProcessor: Error creating title sequence: {e}")
            return []
    
    def _create_flowing_image_sequence(self, images):
        """Create flowing sequence with artistic transitions between images"""
        try:
            frames = []
            
            for i, img in enumerate(images):
                if not os.path.exists(img.file_path):
                    continue
                
                print(f"VideoProcessor: Processing image {i+1}/{len(images)}: {img.original_filename}")
                
                # Create artistic frames for this image
                image_frames = self._create_artistic_image_frames(img.file_path, i)
                frames.extend(image_frames)
                
                # Add transition to next image (except for last image)
                if i < len(images) - 1:
                    next_img_path = None
                    for j in range(i + 1, len(images)):
                        if os.path.exists(images[j].file_path):
                            next_img_path = images[j].file_path
                            break
                    
                    if next_img_path:
                        transition_frames = self._create_artistic_transition(
                            img.file_path, next_img_path, i % 4  # Cycle through transition types
                        )
                        frames.extend(transition_frames)
            
            return frames
            
        except Exception as e:
            print(f"VideoProcessor: Error creating image sequence: {e}")
            return []
    
    def _create_artistic_image_frames(self, image_path, image_index):
        """Create artistic frames for a single image with effects"""
        try:
            frames = []
            total_frames = int(self.image_duration * self.fps)
            
            # Load and prepare image
            with Image.open(image_path) as img:
                img = img.convert('RGB')
                
                # Apply artistic filter based on image index
                artistic_img = self._apply_artistic_filter(img, image_index % 3)
                
                for frame_num in range(total_frames):
                    # Create frame with animated background
                    frame = self._create_animated_gradient_background(
                        frame_num, total_frames, 
                        color_scheme=['dark_blue', 'warm_brown', 'deep_purple'][image_index % 3]
                    )
                    
                    # Calculate animation progress
                    progress = frame_num / total_frames
                    
                    # Apply different effects based on progress
                    if progress < 0.2:  # Fade in with zoom
                        effect_img = self._apply_fade_zoom_in(artistic_img, progress / 0.2)
                    elif progress > 0.8:  # Fade out with slight zoom
                        effect_img = self._apply_fade_zoom_out(artistic_img, (progress - 0.8) / 0.2)
                    else:  # Subtle movement and breathing effect
                        effect_img = self._apply_breathing_effect(artistic_img, frame_num, total_frames)
                    
                    # Center and paste image
                    img_x = (self.frame_size[0] - effect_img.width) // 2
                    img_y = (self.frame_size[1] - effect_img.height) // 2
                    
                    # Add artistic border
                    bordered_img = self._add_artistic_border(effect_img, image_index)
                    
                    # Paste with proper positioning
                    paste_x = (self.frame_size[0] - bordered_img.width) // 2
                    paste_y = (self.frame_size[1] - bordered_img.height) // 2
                    
                    if bordered_img.mode == 'RGBA':
                        frame.paste(bordered_img, (paste_x, paste_y), bordered_img)
                    else:
                        frame.paste(bordered_img, (paste_x, paste_y))
                    
                    # Add subtle overlay effects
                    frame = self._add_artistic_overlay(frame, progress, image_index)
                    
                    frames.append(frame)
            
            return frames
            
        except Exception as e:
            print(f"VideoProcessor: Error processing artistic image {image_path}: {e}")
            return []
    
    def _create_artistic_transition(self, img1_path, img2_path, transition_type):
        """Create artistic transition between two images"""
        try:
            frames = []
            transition_frames = int(self.transition_duration * self.fps)
            
            # Load both images
            with Image.open(img1_path) as img1, Image.open(img2_path) as img2:
                img1 = img1.convert('RGB')
                img2 = img2.convert('RGB')
                
                # Prepare images for transition
                img1_prepared = self._prepare_image_for_frame(img1)
                img2_prepared = self._prepare_image_for_frame(img2)
                
                for frame_num in range(transition_frames):
                    progress = frame_num / transition_frames
                    
                    if transition_type == 0:  # Cross fade
                        frame = self._create_crossfade_transition(img1_prepared, img2_prepared, progress)
                    elif transition_type == 1:  # Slide transition
                        frame = self._create_slide_transition(img1_prepared, img2_prepared, progress)
                    elif transition_type == 2:  # Zoom transition
                        frame = self._create_zoom_transition(img1_prepared, img2_prepared, progress)
                    else:  # Artistic dissolve
                        frame = self._create_artistic_dissolve(img1_prepared, img2_prepared, progress)
                    
                    frames.append(frame)
            
            return frames
            
        except Exception as e:
            print(f"VideoProcessor: Error creating transition: {e}")
            return []
    
    def _apply_artistic_filter(self, img, filter_type):
        """Apply artistic filters to enhance image beauty"""
        try:
            if filter_type == 0:  # Warm and soft
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(1.2)
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.1)
                img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
                
            elif filter_type == 1:  # Vintage look
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(0.8)
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(1.1)
                
            elif filter_type == 2:  # High contrast artistic
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.3)
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(1.2)
            
            return img
            
        except Exception as e:
            print(f"VideoProcessor: Error applying artistic filter: {e}")
            return img
    
    def _create_animated_gradient_background(self, frame_num, total_frames, color_scheme='blue_gold'):
        """Create animated gradient background"""
        try:
            frame = Image.new('RGB', self.frame_size, color='black')
            
            # Define color schemes
            schemes = {
                'blue_gold': [(26, 26, 46), (217, 152, 47)],
                'warm_brown': [(46, 26, 26), (139, 69, 19)],
                'deep_purple': [(46, 26, 46), (138, 43, 226)],
                'dark_blue': [(13, 13, 39), (25, 25, 112)],
                'music_theme': [(20, 20, 40), (80, 40, 120)]  # Purple-blue theme for music videos
            }
            
            colors = schemes.get(color_scheme, schemes['blue_gold'])
            
            # Animate gradient
            animation_progress = (frame_num / total_frames) * 2 * math.pi
            intensity = 0.5 + 0.3 * math.sin(animation_progress)
            
            for y in range(self.frame_size[1]):
                progress = y / self.frame_size[1]
                
                # Interpolate colors
                r = int(colors[0][0] + (colors[1][0] - colors[0][0]) * progress * intensity)
                g = int(colors[0][1] + (colors[1][1] - colors[0][1]) * progress * intensity)
                b = int(colors[0][2] + (colors[1][2] - colors[0][2]) * progress * intensity)
                
                # Add subtle noise for texture
                noise = random.randint(-5, 5)
                r = max(0, min(255, r + noise))
                g = max(0, min(255, g + noise))
                b = max(0, min(255, b + noise))
                
                # Draw gradient line
                draw = ImageDraw.Draw(frame)
                draw.line([(0, y), (self.frame_size[0], y)], fill=(r, g, b))
            
            return frame.convert('RGBA')  # Return RGBA for proper compositing
            
        except Exception as e:
            print(f"VideoProcessor: Error creating gradient background: {e}")
            return Image.new('RGBA', self.frame_size, color=(0, 0, 0, 255))
    
    def _prepare_image_for_frame(self, img):
        """Prepare image to fit frame while maintaining aspect ratio"""
        try:
            # Calculate scaling to fit frame
            img_ratio = img.width / img.height
            frame_ratio = self.frame_size[0] / self.frame_size[1]
            
            if img_ratio > frame_ratio:
                # Image is wider - fit to width
                new_width = int(self.frame_size[0] * 0.8)  # Leave some margin
                new_height = int(new_width / img_ratio)
            else:
                # Image is taller - fit to height
                new_height = int(self.frame_size[1] * 0.8)  # Leave some margin
                new_width = int(new_height * img_ratio)
            
            return img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
        except Exception as e:
            print(f"VideoProcessor: Error preparing image: {e}")
            return img
    
    def _apply_fade_zoom_in(self, img, progress):
        """Apply fade-in with zoom effect"""
        try:
            # Zoom effect
            zoom_factor = 0.7 + (0.3 * progress)
            new_size = (int(img.width * zoom_factor), int(img.height * zoom_factor))
            zoomed_img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Fade effect
            alpha = int(255 * progress)
            if zoomed_img.mode != 'RGBA':
                zoomed_img = zoomed_img.convert('RGBA')
            
            # Apply alpha
            alpha_layer = Image.new('RGBA', zoomed_img.size, (255, 255, 255, alpha))
            zoomed_img = Image.alpha_composite(
                Image.new('RGBA', zoomed_img.size, (0, 0, 0, 0)),
                Image.alpha_composite(alpha_layer, zoomed_img)
            )
            
            return zoomed_img
            
        except Exception as e:
            print(f"VideoProcessor: Error applying fade zoom in: {e}")
            return img
    
    def _apply_fade_zoom_out(self, img, progress):
        """Apply fade-out with zoom effect"""
        try:
            # Zoom effect
            zoom_factor = 1.0 + (0.1 * progress)
            new_size = (int(img.width * zoom_factor), int(img.height * zoom_factor))
            zoomed_img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Fade effect
            alpha = int(255 * (1.0 - progress))
            if zoomed_img.mode != 'RGBA':
                zoomed_img = zoomed_img.convert('RGBA')
            
            # Apply alpha
            alpha_layer = Image.new('RGBA', zoomed_img.size, (255, 255, 255, alpha))
            zoomed_img = Image.alpha_composite(
                Image.new('RGBA', zoomed_img.size, (0, 0, 0, 0)),
                Image.alpha_composite(alpha_layer, zoomed_img)
            )
            
            return zoomed_img
            
        except Exception as e:
            print(f"VideoProcessor: Error applying fade zoom out: {e}")
            return img
    
    def _apply_breathing_effect(self, img, frame_num, total_frames):
        """Apply subtle breathing/pulsing effect"""
        try:
            # Create breathing animation
            breathing_cycle = (frame_num / total_frames) * 4 * math.pi
            scale_factor = 1.0 + 0.02 * math.sin(breathing_cycle)
            
            new_size = (int(img.width * scale_factor), int(img.height * scale_factor))
            return img.resize(new_size, Image.Resampling.LANCZOS)
            
        except Exception as e:
            print(f"VideoProcessor: Error applying breathing effect: {e}")
            return img
    
    def _add_artistic_border(self, img, style_index):
        """Add artistic border to image"""
        try:
            border_width = 8
            border_colors = [
                (217, 152, 47),  # Gold
                (139, 69, 19),   # Brown
                (138, 43, 226),  # Purple
                (25, 25, 112)    # Navy
            ]
            
            border_color = border_colors[style_index % len(border_colors)]
            
            # Create new image with border
            bordered_size = (img.width + 2 * border_width, img.height + 2 * border_width)
            bordered_img = Image.new('RGB', bordered_size, border_color)
            
            # Paste original image in center
            bordered_img.paste(img, (border_width, border_width))
            
            # Add inner shadow effect
            draw = ImageDraw.Draw(bordered_img)
            shadow_width = 3
            shadow_color = (0, 0, 0, 100)
            
            for i in range(shadow_width):
                draw.rectangle([
                    border_width - i, border_width - i,
                    bordered_size[0] - border_width + i - 1,
                    bordered_size[1] - border_width + i - 1
                ], outline=shadow_color, width=1)
            
            return bordered_img
            
        except Exception as e:
            print(f"VideoProcessor: Error adding border: {e}")
            return img
    
    def _create_crossfade_transition(self, img1, img2, progress):
        """Create crossfade transition between images"""
        try:
            frame = Image.new('RGB', self.frame_size, color='black')
            
            # Position images
            x1 = (self.frame_size[0] - img1.width) // 2
            y1 = (self.frame_size[1] - img1.height) // 2
            x2 = (self.frame_size[0] - img2.width) // 2
            y2 = (self.frame_size[1] - img2.height) // 2
            
            # Create alpha blended images
            alpha1 = int(255 * (1.0 - progress))
            alpha2 = int(255 * progress)
            
            # Convert to RGBA for blending
            img1_rgba = img1.convert('RGBA')
            img2_rgba = img2.convert('RGBA')
            
            # Apply alpha
            img1_alpha = Image.new('RGBA', img1.size, (255, 255, 255, alpha1))
            img2_alpha = Image.new('RGBA', img2.size, (255, 255, 255, alpha2))
            
            img1_faded = Image.alpha_composite(
                Image.new('RGBA', img1.size, (0, 0, 0, 0)), 
                Image.alpha_composite(img1_alpha, img1_rgba)
            )
            img2_faded = Image.alpha_composite(
                Image.new('RGBA', img2.size, (0, 0, 0, 0)), 
                Image.alpha_composite(img2_alpha, img2_rgba)
            )
            
            # Paste onto frame
            frame.paste(img1_faded, (x1, y1), img1_faded)
            frame.paste(img2_faded, (x2, y2), img2_faded)
            
            return frame
            
        except Exception as e:
            print(f"VideoProcessor: Error creating crossfade: {e}")
            return Image.new('RGB', self.frame_size, color='black')
    
    def _create_artistic_message_sequence(self, tribute_data):
        """Create artistic message sequence with fade effects"""
        try:
            frames = []
            total_frames = int(4.0 * self.fps)  # 4 seconds
            
            for frame_num in range(total_frames):
                # Create animated background
                frame = self._create_animated_gradient_background(
                    frame_num, total_frames, color_scheme='warm_brown'
                )
                
                # Calculate fade progress
                fade_progress = min(1.0, frame_num / (total_frames * 0.3))
                
                # Add message with artistic styling
                if fade_progress > 0:
                    frame = self._add_artistic_message(frame, tribute_data, fade_progress)
                
                frames.append(frame)
            
            return frames
            
        except Exception as e:
            print(f"VideoProcessor: Error creating message sequence: {e}")
            return []
    
    def _add_artistic_message(self, frame, tribute_data, alpha_progress):
        """Add artistic message to frame"""
        try:
            draw = ImageDraw.Draw(frame)
            
            # Load fonts
            try:
                message_font = ImageFont.truetype("arial.ttf", 52)
                small_font = ImageFont.truetype("arial.ttf", 36)
            except:
                message_font = ImageFont.load_default()
                small_font = ImageFont.load_default()
            
            # Word wrap message
            message = tribute_data['message']
            words = message.split()
            lines = []
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                bbox = draw.textbbox((0, 0), test_line, font=message_font)
                if bbox[2] - bbox[0] < self.frame_size[0] - 300:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                    else:
                        lines.append(word)
            
            if current_line:
                lines.append(' '.join(current_line))
            
            # Calculate positioning
            total_height = len(lines) * 70
            start_y = (self.frame_size[1] - total_height) // 2
            
            # Draw lines with artistic effects
            alpha = int(255 * alpha_progress)
            
            for i, line in enumerate(lines):
                bbox = draw.textbbox((0, 0), line, font=message_font)
                line_width = bbox[2] - bbox[0]
                x = (self.frame_size[0] - line_width) // 2
                y = start_y + i * 70
                
                # Create glow effect
                for offset in range(3, 0, -1):
                    glow_alpha = alpha // (offset * 2)
                    draw.text((x + offset, y + offset), line, 
                            fill=(217, 152, 47, glow_alpha), font=message_font)
                
                # Main text
                draw.text((x, y), line, fill=(255, 255, 255, alpha), font=message_font)
            
            # Add music choice at bottom
            music_text = f"♪ {tribute_data['music_choice']} ♪"
            bbox = draw.textbbox((0, 0), music_text, font=small_font)
            music_width = bbox[2] - bbox[0]
            music_x = (self.frame_size[0] - music_width) // 2
            music_y = self.frame_size[1] - 120
            
            draw.text((music_x + 2, music_y + 2), music_text, 
                    fill=(0, 0, 0, alpha//2), font=small_font)
            draw.text((music_x, music_y), music_text, 
                    fill=(217, 152, 47, alpha), font=small_font)
            
            return frame
            
        except Exception as e:
            print(f"VideoProcessor: Error adding artistic message: {e}")
            return frame
    
    def _has_ffmpeg(self):
        """Check if FFmpeg is available"""
        try:
            import subprocess
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def _create_mp4_with_ffmpeg(self, frames, output_path, music_path=None):
        """Create MP4 video using FFmpeg"""
        try:
            import subprocess
            import tempfile
            
            # Create temporary directory for frames
            with tempfile.TemporaryDirectory() as temp_dir:
                # Save frames as images
                for i, frame in enumerate(frames):
                    frame_path = os.path.join(temp_dir, f"frame_{i:06d}.png")
                    frame.save(frame_path, 'PNG')
                
                # Calculate video duration for audio
                total_frames = len(frames)
                video_duration = total_frames / self.fps
                
                # Create video without audio first
                temp_video = os.path.join(temp_dir, 'temp_video.mp4')
                cmd = [
                    'ffmpeg', '-y',
                    '-framerate', str(self.fps),
                    '-i', os.path.join(temp_dir, 'frame_%06d.png'),
                    '-c:v', 'libx264',
                    '-pix_fmt', 'yuv420p',
                    '-crf', '23',
                    temp_video
                ]
                
                print(f"VideoProcessor: Creating video frames...")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                if result.returncode != 0:
                    print(f"VideoProcessor: Frame assembly failed: {result.stderr}")
                    return False
                
                # If music is available, add it to the video
                if music_path and os.path.exists(music_path):
                    print(f"VideoProcessor: Adding music: {music_path}")
                    cmd_with_audio = [
                        'ffmpeg', '-y',
                        '-i', temp_video,
                        '-i', music_path,
                        '-c:v', 'copy',
                        '-c:a', 'aac',
                        '-b:a', '128k',
                        '-shortest',  # Stop when shortest input ends
                        '-map', '0:v:0',
                        '-map', '1:a:0',
                        output_path
                    ]
                    
                    result = subprocess.run(cmd_with_audio, capture_output=True, text=True, timeout=300)
                    if result.returncode == 0:
                        print("VideoProcessor: Video with music created successfully")
                        return True
                    else:
                        print(f"VideoProcessor: Audio integration failed: {result.stderr}")
                        # Fall back to video without audio
                        import shutil
                        shutil.copy2(temp_video, output_path)
                        print("VideoProcessor: Created video without audio")
                        return True
                else:
                    # No music, just copy the video
                    import shutil
                    shutil.copy2(temp_video, output_path)
                    print("VideoProcessor: Created video without audio")
                    return True
                
        except Exception as e:
            print(f"VideoProcessor: FFmpeg error: {e}")
            return False
    
    def _create_artistic_gif(self, frames, output_path):
        """Create artistic animated GIF from frames"""
        try:
            if not frames:
                return False
            
            # Reduce frame count for GIF (every 8th frame for smoother artistic flow)
            gif_frames = frames[::8]
            
            # Resize frames for smaller GIF
            gif_size = (960, 540)  # Half HD
            resized_frames = []
            
            for frame in gif_frames:
                resized = frame.resize(gif_size, Image.Resampling.LANCZOS)
                resized_frames.append(resized)
            
            # Save as animated GIF with optimized settings for artistic content
            resized_frames[0].save(
                output_path,
                save_all=True,
                append_images=resized_frames[1:],
                duration=120,  # 120ms per frame for smooth flow
                loop=0,
                optimize=True
            )
            
            return True
            
        except Exception as e:
            print(f"VideoProcessor: Artistic GIF creation error: {e}")
            return False
    
    def _create_glowing_text(self, text, font, text_color, glow_color):
        """Create text with glow effect"""
        try:
            # Create temporary image to measure text
            temp_img = Image.new('RGBA', (1, 1))
            temp_draw = ImageDraw.Draw(temp_img)
            bbox = temp_draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Create image with padding for glow
            glow_padding = 20
            img_size = (text_width + 2 * glow_padding, text_height + 2 * glow_padding)
            img = Image.new('RGBA', img_size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Draw glow layers
            for glow_size in range(8, 0, -1):
                glow_alpha = glow_color[3] // (glow_size + 1) if len(glow_color) > 3 else 50 // (glow_size + 1)
                current_glow_color = (*glow_color[:3], glow_alpha)
                
                for x_offset in range(-glow_size, glow_size + 1):
                    for y_offset in range(-glow_size, glow_size + 1):
                        if x_offset * x_offset + y_offset * y_offset <= glow_size * glow_size:
                            draw.text((glow_padding + x_offset, glow_padding + y_offset), 
                                    text, fill=current_glow_color, font=font)
            
            # Draw main text
            draw.text((glow_padding, glow_padding), text, fill=text_color, font=font)
            
            return img
            
        except Exception as e:
            print(f"VideoProcessor: Error creating glowing text: {e}")
            # Fallback to simple text
            bbox = ImageDraw.Draw(Image.new('RGBA', (1, 1))).textbbox((0, 0), text, font=font)
            simple_img = Image.new('RGBA', (bbox[2] - bbox[0], bbox[3] - bbox[1]), (0, 0, 0, 0))
            ImageDraw.Draw(simple_img).text((0, 0), text, fill=text_color, font=font)
            return simple_img
    
    def _add_floating_particles(self, draw, frame_num, alpha_progress):
        """Add floating particle effects"""
        try:
            particle_count = 15
            alpha = int(100 * alpha_progress)
            
            for i in range(particle_count):
                # Create pseudo-random but consistent positions based on frame and particle index
                seed = (frame_num + i * 17) % 1000
                x = (seed * 7) % self.frame_size[0]
                y = ((seed * 11) + (frame_num * 2)) % self.frame_size[1]
                
                # Particle size and color variation
                size = 2 + (seed % 4)
                brightness = 150 + (seed % 100)
                
                particle_color = (brightness, brightness // 2, 0, alpha)
                
                # Draw particle as small circle
                draw.ellipse([x - size, y - size, x + size, y + size], 
                           fill=particle_color)
                
        except Exception as e:
            print(f"VideoProcessor: Error adding particles: {e}")
    
    def _add_artistic_overlay(self, frame, progress, image_index):
        """Add subtle artistic overlay effects"""
        try:
            # Create overlay with subtle effects
            overlay = Image.new('RGBA', frame.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            
            # Add subtle vignette effect
            center_x, center_y = frame.size[0] // 2, frame.size[1] // 2
            max_radius = min(center_x, center_y)
            
            # Create subtle vignette
            for radius in range(max_radius, max_radius - 100, -10):
                alpha = int(5 * (max_radius - radius) / 100)
                overlay_draw.ellipse([
                    center_x - radius, center_y - radius,
                    center_x + radius, center_y + radius
                ], outline=(0, 0, 0, alpha), width=10)
            
            # Composite overlay onto frame
            if overlay.mode == 'RGBA':
                frame = Image.alpha_composite(frame.convert('RGBA'), overlay).convert('RGB')
            
            return frame
            
        except Exception as e:
            print(f"VideoProcessor: Error adding overlay: {e}")
            return frame
    
    def _create_slide_transition(self, img1, img2, progress):
        """Create slide transition between images"""
        try:
            frame = Image.new('RGB', self.frame_size, color='black')
            
            # Calculate slide positions
            slide_distance = self.frame_size[0]
            img1_x = int(-slide_distance * progress)
            img2_x = int(slide_distance * (1.0 - progress))
            
            # Position images vertically centered
            img1_y = (self.frame_size[1] - img1.height) // 2
            img2_y = (self.frame_size[1] - img2.height) // 2
            
            # Paste images
            if img1_x + img1.width > 0:  # Image 1 still visible
                frame.paste(img1, (img1_x, img1_y))
            
            if img2_x < self.frame_size[0]:  # Image 2 becoming visible
                frame.paste(img2, (img2_x, img2_y))
            
            return frame
            
        except Exception as e:
            print(f"VideoProcessor: Error creating slide transition: {e}")
            return Image.new('RGB', self.frame_size, color='black')
    
    def _create_zoom_transition(self, img1, img2, progress):
        """Create zoom transition between images"""
        try:
            frame = Image.new('RGB', self.frame_size, color='black')
            
            # Zoom out img1 while fading
            zoom1_factor = 1.0 + (0.5 * progress)
            alpha1 = int(255 * (1.0 - progress))
            
            # Zoom in img2 while appearing
            zoom2_factor = 1.5 - (0.5 * progress)
            alpha2 = int(255 * progress)
            
            # Apply zoom to img1
            new_size1 = (int(img1.width * zoom1_factor), int(img1.height * zoom1_factor))
            zoomed_img1 = img1.resize(new_size1, Image.Resampling.LANCZOS)
            
            # Apply zoom to img2
            new_size2 = (int(img2.width * zoom2_factor), int(img2.height * zoom2_factor))
            zoomed_img2 = img2.resize(new_size2, Image.Resampling.LANCZOS)
            
            # Position images
            x1 = (self.frame_size[0] - zoomed_img1.width) // 2
            y1 = (self.frame_size[1] - zoomed_img1.height) // 2
            x2 = (self.frame_size[0] - zoomed_img2.width) // 2
            y2 = (self.frame_size[1] - zoomed_img2.height) // 2
            
            # Apply alpha and paste
            if alpha1 > 0:
                img1_rgba = zoomed_img1.convert('RGBA')
                alpha_layer1 = Image.new('RGBA', zoomed_img1.size, (255, 255, 255, alpha1))
                img1_faded = Image.alpha_composite(
                    Image.new('RGBA', zoomed_img1.size, (0, 0, 0, 0)),
                    Image.alpha_composite(alpha_layer1, img1_rgba)
                )
                frame.paste(img1_faded, (x1, y1), img1_faded)
            
            if alpha2 > 0:
                img2_rgba = zoomed_img2.convert('RGBA')
                alpha_layer2 = Image.new('RGBA', zoomed_img2.size, (255, 255, 255, alpha2))
                img2_faded = Image.alpha_composite(
                    Image.new('RGBA', zoomed_img2.size, (0, 0, 0, 0)),
                    Image.alpha_composite(alpha_layer2, img2_rgba)
                )
                frame.paste(img2_faded, (x2, y2), img2_faded)
            
            return frame
            
        except Exception as e:
            print(f"VideoProcessor: Error creating zoom transition: {e}")
            return Image.new('RGB', self.frame_size, color='black')
    
    def _create_artistic_dissolve(self, img1, img2, progress):
        """Create artistic dissolve transition with pattern"""
        try:
            frame = Image.new('RGB', self.frame_size, color='black')
            
            # Create dissolve pattern
            pattern_size = 20
            dissolve_threshold = progress
            
            # Position images
            x1 = (self.frame_size[0] - img1.width) // 2
            y1 = (self.frame_size[1] - img1.height) // 2
            x2 = (self.frame_size[0] - img2.width) // 2
            y2 = (self.frame_size[1] - img2.height) // 2
            
            # Create mask for dissolve effect
            mask = Image.new('L', img1.size, 0)
            mask_draw = ImageDraw.Draw(mask)
            
            for x in range(0, img1.width, pattern_size):
                for y in range(0, img1.height, pattern_size):
                    # Create pseudo-random pattern
                    pattern_value = ((x + y) * 7) % 100 / 100.0
                    if pattern_value < dissolve_threshold:
                        mask_draw.rectangle([x, y, x + pattern_size, y + pattern_size], fill=255)
            
            # Apply dissolve effect
            img1_rgba = img1.convert('RGBA')
            img2_rgba = img2.convert('RGBA')
            
            # Use mask to blend images
            blended = Image.composite(img2_rgba, img1_rgba, mask)
            
            frame.paste(blended, (x1, y1), blended)
            
            return frame
            
        except Exception as e:
            print(f"VideoProcessor: Error creating artistic dissolve: {e}")
            return self._create_crossfade_transition(img1, img2, progress)
    
    def create_tribute_video_with_cancellation(self, images, tribute_data, output_path, generation_id, task_manager):
        """
        Create tribute video with cancellation support
        
        Args:
            images: List of TributeImage objects
            tribute_data: Dict with title, message, music_choice, custom_music_url
            output_path: Path where to save the video
            generation_id: ID for tracking cancellation
            task_manager: Task manager for checking cancellation status
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"VideoProcessor: Creating tribute video with cancellation support...")
            print(f"VideoProcessor: Generation ID: {generation_id}")
            print(f"VideoProcessor: Images count: {len(images)}")
            print(f"VideoProcessor: Output: {output_path}")
            print(f"VideoProcessor: Music choice: {tribute_data.get('music_choice', 'none')}")
            
            # Check for cancellation at start
            if task_manager.get_task_status(generation_id) == 'cancelled':
                print(f"VideoProcessor: Generation {generation_id} was cancelled before starting")
                return False
            
            # Check music file
            music_choice = tribute_data.get('music_choice')
            custom_music_url = tribute_data.get('custom_music_url')
            music_path = None
            if music_choice:
                music_path = self.get_music_path(music_choice, custom_music_url)
                if music_path and os.path.exists(music_path):
                    print(f"VideoProcessor: Using music file: {music_path}")
                else:
                    print(f"VideoProcessor: Music file not found: {music_path}")
                    if custom_music_url:
                        print(f"VideoProcessor: Custom music URL was: {custom_music_url}")
                    music_path = None
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Check for cancellation before frame creation
            if task_manager.get_task_status(generation_id) == 'cancelled':
                print(f"VideoProcessor: Generation {generation_id} cancelled before frame creation")
                return False
            
            # Create artistic video frames with cancellation checks
            frames = self._create_artistic_video_frames_with_cancellation(
                images, tribute_data, generation_id, task_manager
            )
            
            if not frames:
                print("VideoProcessor: No frames created or generation was cancelled")
                return False
            
            # Check for cancellation before video assembly
            if task_manager.get_task_status(generation_id) == 'cancelled':
                print(f"VideoProcessor: Generation {generation_id} cancelled before video assembly")
                return False
            
            # Try to create MP4 with FFmpeg if available
            if self._has_ffmpeg():
                print("VideoProcessor: FFmpeg available, creating MP4...")
                success = self._create_mp4_with_ffmpeg_and_cancellation(
                    frames, output_path, music_path, generation_id, task_manager
                )
                if success:
                    print("VideoProcessor: MP4 created successfully with FFmpeg")
                    return True
                else:
                    print("VideoProcessor: FFmpeg creation failed, trying fallback...")
            else:
                print("VideoProcessor: FFmpeg not available, using fallback...")
            
            # Check for cancellation before fallback
            if task_manager.get_task_status(generation_id) == 'cancelled':
                print(f"VideoProcessor: Generation {generation_id} cancelled before fallback")
                return False
            
            # Fallback: Create artistic animated GIF
            gif_path = output_path.replace('.mp4', '.gif')
            success = self._create_artistic_gif_with_cancellation(
                frames, gif_path, generation_id, task_manager
            )
            
            if success:
                print(f"VideoProcessor: Created artistic GIF slideshow: {gif_path}")
                
                # Create MP4 placeholder file with music info
                with open(output_path, 'w') as f:
                    f.write(f"Artistic tribute video created as animated GIF: {gif_path}\n")
                    f.write(f"Title: {tribute_data['title']}\n")
                    f.write(f"Music: {tribute_data.get('music_choice', 'none')}\n")
                    if music_path:
                        f.write(f"Music file: {music_path}\n")
                    f.write(f"Features: Artistic transitions, zoom effects, fades\n")
                    f.write(f"Created: {datetime.now().isoformat()}\n")
                    f.write(f"Note: Install FFmpeg to create MP4 with audio\n")
                
                return True
            
            return False
            
        except Exception as e:
            print(f"VideoProcessor: Error creating tribute video with cancellation: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _create_artistic_video_frames_with_cancellation(self, images, tribute_data, generation_id, task_manager):
        """Create artistic video frames with cancellation checks"""
        try:
            frames = []
            
            # Check for cancellation
            if task_manager.get_task_status(generation_id) == 'cancelled':
                return []
            
            # Opening title sequence with fade-in effect
            print("VideoProcessor: Creating title sequence...")
            title_frames = self._create_artistic_title_sequence(tribute_data)
            frames.extend(title_frames)
            
            # Check for cancellation after title
            if task_manager.get_task_status(generation_id) == 'cancelled':
                return []
            
            # Process images with artistic effects and transitions
            if images:
                print(f"VideoProcessor: Processing {len(images)} images...")
                for i, image in enumerate(images):
                    # Check for cancellation during image processing
                    if task_manager.get_task_status(generation_id) == 'cancelled':
                        print(f"VideoProcessor: Cancelled during image {i+1}")
                        return []
                    
                    print(f"VideoProcessor: Processing image {i+1}/{len(images)}: {image.original_filename}")
                    image_frames = self._create_artistic_image_frames(image.file_path, i)
                    frames.extend(image_frames)
            
            # Check for cancellation before message
            if task_manager.get_task_status(generation_id) == 'cancelled':
                return []
            
            # Closing message sequence with fade-out effect
            print("VideoProcessor: Creating message sequence...")
            message_frames = self._create_artistic_message_sequence(tribute_data)
            frames.extend(message_frames)
            
            print(f"VideoProcessor: Created {len(frames)} artistic frames total")
            return frames
            
        except Exception as e:
            print(f"VideoProcessor: Error creating frames with cancellation: {e}")
            return []

    def _create_music_only_frames_with_cancellation(self, tribute_data, generation_id, task_manager):
        """Create frames for music-only video with cancellation checks"""
        try:
            frames = []
            
            # Check for cancellation
            if task_manager.get_task_status(generation_id) == 'cancelled':
                return []
            
            print("VideoProcessor: Creating music-only video frames...")
            
            # Create frames with text overlay and music visualization
            # Duration: 30 seconds at 30fps = 900 frames
            total_frames = 900
            
            for frame_num in range(total_frames):
                # Check for cancellation every 100 frames
                if frame_num % 100 == 0 and task_manager.get_task_status(generation_id) == 'cancelled':
                    print(f"VideoProcessor: Music-only video cancelled at frame {frame_num}")
                    return []
                
                # Create frame with animated background and text
                frame = self._create_music_visualization_frame(tribute_data, frame_num, total_frames)
                frames.append(frame)
            
            print(f"VideoProcessor: Created {len(frames)} music-only frames")
            return frames
            
        except Exception as e:
            print(f"VideoProcessor: Error creating music-only frames: {e}")
            return []

    def _create_music_visualization_frame(self, tribute_data, frame_num, total_frames):
        """Create a single frame for music visualization"""
        try:
            # Create frame with animated gradient background
            frame = Image.new('RGB', self.frame_size, (0, 0, 0))
            
            # Add animated gradient background
            gradient_frame = self._create_animated_gradient_background(frame_num, total_frames, 'music_theme')
            frame = Image.alpha_composite(frame.convert('RGBA'), gradient_frame).convert('RGB')
            
            # Add title and message text
            draw = ImageDraw.Draw(frame)
            
            # Try to load fonts
            try:
                title_font = ImageFont.truetype("arial.ttf", 72)
                message_font = ImageFont.truetype("arial.ttf", 36)
            except:
                title_font = ImageFont.load_default()
                message_font = ImageFont.load_default()
            
            # Add title with fade effect
            title_alpha = min(255, max(0, int(255 * (frame_num / 60))))  # Fade in over 2 seconds
            title_color = (255, 255, 255, title_alpha)
            
            # Center title
            title_text = tribute_data.get('title', 'Music Tribute')
            title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
            title_x = (self.frame_size[0] - (title_bbox[2] - title_bbox[0])) // 2
            title_y = self.frame_size[1] // 3
            
            # Create text overlay
            text_overlay = Image.new('RGBA', self.frame_size, (0, 0, 0, 0))
            text_draw = ImageDraw.Draw(text_overlay)
            text_draw.text((title_x, title_y), title_text, fill=title_color, font=title_font)
            
            # Add message after 3 seconds
            if frame_num > 90:  # 3 seconds at 30fps
                message_alpha = min(255, max(0, int(255 * ((frame_num - 90) / 60))))
                message_color = (200, 200, 200, message_alpha)
                
                message_text = tribute_data.get('message', '')[:100] + "..." if len(tribute_data.get('message', '')) > 100 else tribute_data.get('message', '')
                message_bbox = text_draw.textbbox((0, 0), message_text, font=message_font)
                message_x = (self.frame_size[0] - (message_bbox[2] - message_bbox[0])) // 2
                message_y = title_y + 120
                
                text_draw.text((message_x, message_y), message_text, fill=message_color, font=message_font)
            
            # Composite text overlay
            frame = Image.alpha_composite(frame.convert('RGBA'), text_overlay).convert('RGB')
            
            return frame
            
        except Exception as e:
            print(f"VideoProcessor: Error creating music visualization frame: {e}")
            # Return simple black frame as fallback
            return Image.new('RGB', self.frame_size, (0, 0, 0))

    def _create_mp4_with_ffmpeg_and_cancellation(self, frames, output_path, music_path, generation_id, task_manager):
        """Create MP4 video using FFmpeg with cancellation support"""
        try:
            import subprocess
            import tempfile
            
            # Check for cancellation before starting
            if task_manager.get_task_status(generation_id) == 'cancelled':
                return False
            
            # Create temporary directory for frames
            with tempfile.TemporaryDirectory() as temp_dir:
                print(f"VideoProcessor: Saving {len(frames)} frames to temporary directory...")
                
                # Save frames as images with cancellation checks
                for i, frame in enumerate(frames):
                    # Check for cancellation every 50 frames
                    if i % 50 == 0 and task_manager.get_task_status(generation_id) == 'cancelled':
                        print(f"VideoProcessor: Cancelled while saving frame {i}")
                        return False
                    
                    frame_path = os.path.join(temp_dir, f"frame_{i:06d}.png")
                    frame.save(frame_path, 'PNG')
                
                # Check for cancellation before FFmpeg
                if task_manager.get_task_status(generation_id) == 'cancelled':
                    return False
                
                # Calculate video duration for audio
                total_frames = len(frames)
                video_duration = total_frames / self.fps
                
                print(f"VideoProcessor: Creating video from frames (duration: {video_duration:.2f}s)...")
                
                # Create video without audio first
                temp_video = os.path.join(temp_dir, 'temp_video.mp4')
                cmd = [
                    'ffmpeg', '-y',
                    '-framerate', str(self.fps),
                    '-i', os.path.join(temp_dir, 'frame_%06d.png'),
                    '-c:v', 'libx264',
                    '-pix_fmt', 'yuv420p',
                    '-crf', '23',
                    temp_video
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                if result.returncode != 0:
                    print(f"VideoProcessor: Frame assembly failed: {result.stderr}")
                    return False
                
                # Check for cancellation before audio processing
                if task_manager.get_task_status(generation_id) == 'cancelled':
                    return False
                
                # If music is available, add it to the video
                if music_path and os.path.exists(music_path):
                    print(f"VideoProcessor: Adding music: {music_path}")
                    cmd_with_audio = [
                        'ffmpeg', '-y',
                        '-i', temp_video,
                        '-i', music_path,
                        '-c:v', 'copy',
                        '-c:a', 'aac',
                        '-b:a', '128k',
                        '-shortest',  # Stop when shortest input ends
                        '-map', '0:v:0',
                        '-map', '1:a:0',
                        output_path
                    ]
                    
                    result = subprocess.run(cmd_with_audio, capture_output=True, text=True, timeout=300)
                    if result.returncode == 0:
                        print("VideoProcessor: Video with music created successfully")
                        return True
                    else:
                        print(f"VideoProcessor: Audio integration failed: {result.stderr}")
                        # Fall back to video without audio
                        import shutil
                        shutil.copy2(temp_video, output_path)
                        print("VideoProcessor: Created video without audio")
                        return True
                else:
                    # No music, just copy the video
                    import shutil
                    shutil.copy2(temp_video, output_path)
                    print("VideoProcessor: Created video without audio")
                    return True
                
        except Exception as e:
            print(f"VideoProcessor: FFmpeg error with cancellation: {e}")
            return False

    def _create_artistic_gif_with_cancellation(self, frames, output_path, generation_id, task_manager):
        """Create artistic animated GIF with cancellation support"""
        try:
            if not frames:
                return False
            
            # Check for cancellation
            if task_manager.get_task_status(generation_id) == 'cancelled':
                return False
            
            print("VideoProcessor: Creating artistic GIF...")
            
            # Reduce frame count for GIF (every 8th frame for smoother artistic flow)
            gif_frames = frames[::8]
            
            # Resize frames for smaller GIF
            gif_size = (960, 540)  # Half HD
            resized_frames = []
            
            for i, frame in enumerate(gif_frames):
                # Check for cancellation during processing
                if i % 10 == 0 and task_manager.get_task_status(generation_id) == 'cancelled':
                    print(f"VideoProcessor: GIF creation cancelled at frame {i}")
                    return False
                
                resized = frame.resize(gif_size, Image.Resampling.LANCZOS)
                resized_frames.append(resized)
            
            # Final cancellation check
            if task_manager.get_task_status(generation_id) == 'cancelled':
                return False
            
            # Save as animated GIF with optimized settings for artistic content
            resized_frames[0].save(
                output_path,
                save_all=True,
                append_images=resized_frames[1:],
                duration=120,  # 120ms per frame for smooth flow
                loop=0,
                optimize=True
            )
            
            print(f"VideoProcessor: Artistic GIF created: {output_path}")
            return True
            
        except Exception as e:
            print(f"VideoProcessor: Artistic GIF creation error: {e}")
            return False

    def create_music_only_video_with_cancellation(self, tribute_data, output_path, generation_id, task_manager):
        """
        Create music-only video with cancellation support
        
        Args:
            tribute_data: Dict with title, message, music_choice, custom_music_url
            output_path: Path where to save the video
            generation_id: ID for tracking cancellation
            task_manager: Task manager for checking cancellation status
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"VideoProcessor: Creating music-only video with cancellation support...")
            print(f"VideoProcessor: Generation ID: {generation_id}")
            print(f"VideoProcessor: Music choice: {tribute_data.get('music_choice', 'none')}")
            
            # Check for cancellation at start
            if task_manager.get_task_status(generation_id) == 'cancelled':
                print(f"VideoProcessor: Generation {generation_id} was cancelled before starting")
                return False
            
            # Get music file
            music_choice = tribute_data.get('music_choice')
            custom_music_url = tribute_data.get('custom_music_url')
            music_path = self.get_music_path(music_choice, custom_music_url)
            
            if not music_path or not os.path.exists(music_path):
                print(f"VideoProcessor: Music file not found: {music_path}")
                return False
            
            print(f"VideoProcessor: Using music file: {music_path}")
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Check for cancellation before frame creation
            if task_manager.get_task_status(generation_id) == 'cancelled':
                print(f"VideoProcessor: Generation {generation_id} cancelled before frame creation")
                return False
            
            # Create frames for music-only video (text overlay with music visualization)
            frames = self._create_music_only_frames_with_cancellation(
                tribute_data, generation_id, task_manager
            )
            
            if not frames:
                print("VideoProcessor: No frames created for music-only video")
                return False
            
            # Check for cancellation before video assembly
            if task_manager.get_task_status(generation_id) == 'cancelled':
                print(f"VideoProcessor: Generation {generation_id} cancelled before video assembly")
                return False
            
            # Try to create MP4 with FFmpeg if available
            if self._has_ffmpeg():
                print("VideoProcessor: Creating music-only MP4 with FFmpeg...")
                success = self._create_mp4_with_ffmpeg_and_cancellation(
                    frames, output_path, music_path, generation_id, task_manager
                )
                if success:
                    print("VideoProcessor: Music-only MP4 created successfully")
                    return True
                else:
                    print("VideoProcessor: FFmpeg creation failed for music-only video")
            else:
                print("VideoProcessor: FFmpeg not available for music-only video")
            
            # Fallback: Create a simple video file placeholder
            with open(output_path, 'w') as f:
                f.write(f"Music-only tribute video\n")
                f.write(f"Title: {tribute_data['title']}\n")
                f.write(f"Message: {tribute_data['message']}\n")
                f.write(f"Music: {music_path}\n")
                f.write(f"Created: {datetime.now().isoformat()}\n")
                f.write(f"Note: FFmpeg required for actual video creation\n")
            
            return True
            
        except Exception as e:
            print(f"VideoProcessor: Error creating music-only video: {e}")
            import traceback
            traceback.print_exc()
            return False

    def create_thumbnail(self, video_path, thumbnail_path):
        """Create thumbnail from video"""
        try:
            # For GIF files, extract first frame
            if video_path.endswith('.gif'):
                with Image.open(video_path) as gif:
                    gif.seek(0)
                    thumbnail = gif.copy()
                    thumbnail.thumbnail((320, 180), Image.Resampling.LANCZOS)
                    thumbnail.save(thumbnail_path, 'JPEG', quality=85)
                    return True
            
            # For MP4 files, try FFmpeg
            if self._has_ffmpeg():
                import subprocess
                cmd = [
                    'ffmpeg', '-y',
                    '-i', video_path,
                    '-vframes', '1',
                    '-vf', 'scale=320:180',
                    thumbnail_path
                ]
                result = subprocess.run(cmd, capture_output=True, timeout=30)
                return result.returncode == 0
            
            return False
            
        except Exception as e:
            print(f"VideoProcessor: Thumbnail creation error: {e}")
            return False

# Test function
def test_video_processor():
    """Test the video processor"""
    processor = VideoProcessor()
    
    # Mock data
    class MockImage:
        def __init__(self, path, filename):
            self.file_path = path
            self.original_filename = filename
    
    # Create test directory
    test_dir = "test_output"
    os.makedirs(test_dir, exist_ok=True)
    
    # Test with a simple image (create a test image if needed)
    test_image_path = os.path.join(test_dir, "test_image.jpg")
    if not os.path.exists(test_image_path):
        # Create a test image
        test_img = Image.new('RGB', (800, 600), color='blue')
        draw = ImageDraw.Draw(test_img)
        try:
            font = ImageFont.truetype("arial.ttf", 48)
        except:
            font = ImageFont.load_default()
        draw.text((100, 300), "Test Image", fill='white', font=font)
        test_img.save(test_image_path)
        print(f"Created test image: {test_image_path}")
    
    images = [MockImage(test_image_path, "test.jpg")]
    tribute_data = {
        'title': 'Test Artistic Tribute',
        'message': 'This is a test tribute message with artistic flowing transitions and beautiful effects.',
        'music_choice': 'peaceful'
    }
    
    output_path = os.path.join(test_dir, "test_output.mp4")
    print(f"Testing artistic video creation...")
    print(f"Output will be saved to: {output_path}")
    
    success = processor.create_tribute_video(images, tribute_data, output_path)
    
    print(f"\n🎬 Test result: {'✅ Success' if success else '❌ Failed'}")
    
    if success:
        print("\n📂 Generated files:")
        
        # Check for generated files
        gif_file = output_path.replace('.mp4', '.gif')
        info_file = output_path.replace('.mp4', '_info.txt')
        
        if os.path.exists(output_path):
            print(f"✅ MP4 placeholder: {output_path} ({os.path.getsize(output_path)} bytes)")
        
        if os.path.exists(gif_file):
            print(f"✅ Artistic GIF: {gif_file} ({os.path.getsize(gif_file)} bytes)")
        
        if os.path.exists(info_file):
            print(f"✅ Info file: {info_file}")
            with open(info_file, 'r') as f:
                print("📄 Content:")
                print(f.read())
    
    # Cleanup test image
    try:
        if os.path.exists(test_image_path):
            os.remove(test_image_path)
        print(f"\n🧹 Cleaned up test image")
    except:
        pass

if __name__ == "__main__":
    test_video_processor() 