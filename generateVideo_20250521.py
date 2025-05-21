#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 21 14:33:11 2025

@author: arunsasidharan
"""

import os
import random
import cv2
from PIL import Image, ImageDraw, ImageFont
import re

# --- Configuration ---
VIDEO_FILENAME = "random_photos_video.mp4"
IMAGE_DURATION_SECONDS = 3  # How long each image will be displayed
FPS = 1 # Frames per second for the video (1 means each image is one frame)
CAPTION_FONT_SIZE = 300
CAPTION_FONT_COLOR = (255, 255, 255)  # White
CAPTION_BG_COLOR = (0, 0, 0, 128)    # Semi-transparent black background for caption
VIDEO_WIDTH = 1280 # Desired video width (images will be resized to fit)
VIDEO_HEIGHT = 720 # Desired video height

def get_image_files(folder_path):
    """Gets a list of image files from the specified folder."""
    image_files = []
    supported_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')
    if not os.path.isdir(folder_path):
        print(f"Error: Folder not found at {folder_path}")
        return []
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(supported_extensions):
            image_files.append(os.path.join(folder_path, filename))
    if not image_files:
        print(f"No image files found in {folder_path}")
    else:
        print(f"Found {len(image_files)} images.")
    return image_files

def add_caption_to_image(image_path, caption_text):
    """
    Opens an image, adds a caption, and returns the modified PIL Image object.
    Images are resized to fit VIDEO_WIDTH x VIDEO_HEIGHT while maintaining aspect ratio,
    and then placed on a black background of VIDEO_WIDTH x VIDEO_HEIGHT.
    """
    try:
        img = Image.open(image_path).convert("RGBA")

        # --- Resize image to fit within video dimensions while maintaining aspect ratio ---
        img_ratio = img.width / img.height
        vid_ratio = VIDEO_WIDTH / VIDEO_HEIGHT

        if img_ratio > vid_ratio: # Image is wider than video frame
            new_width = VIDEO_WIDTH
            new_height = int(new_width / img_ratio)
        else: # Image is taller than or same aspect ratio as video frame
            new_height = VIDEO_HEIGHT
            new_width = int(new_height * img_ratio)

        img = img.resize((new_width, new_height), Image.LANCZOS)

        # --- Create a new image with a black background ---
        background = Image.new('RGBA', (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0, 255))
        # Calculate position to paste the resized image (centered)
        paste_x = (VIDEO_WIDTH - new_width) // 2
        paste_y = (VIDEO_HEIGHT - new_height) // 2
        background.paste(img, (paste_x, paste_y))
        img = background # Use the background with the pasted image

        # --- Add caption ---
        draw = ImageDraw.Draw(img)
        font = None
        
        # For Windows, common: "arial.ttf", "times.ttf", "cour.ttf"
        # For macOS, common: "Arial.ttf", "Helvetica.ttf", "Times New Roman.ttf"
        # For Linux, common: "DejaVuSans.ttf", "LiberationSans-Regular.ttf" (if installed)
        system_font_name = "Arial.ttf"
        try:
            font = ImageFont.truetype(system_font_name, CAPTION_FONT_SIZE)
            print(f"Using system font: {system_font_name} with size {CAPTION_FONT_SIZE}")
        except IOError:
            print("Default font not found. Using basic PIL font.")
            font = ImageFont.load_default()


        text_bbox = draw.textbbox((0, 0), caption_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        # Position caption at the bottom center
        margin = 10
        x = (img.width - text_width) / 2
        y = img.height - text_height - margin * 2 # Position above bottom edge

        # Add a background rectangle for the text
        rect_x0 = x - margin
        rect_y0 = y - margin
        rect_x1 = x + text_width + margin
        rect_y1 = y + text_height + margin
        draw.rectangle([rect_x0, rect_y0, rect_x1, rect_y1], fill=CAPTION_BG_COLOR)

        draw.text((x, y), caption_text, font=font, fill=CAPTION_FONT_COLOR)
        return img

    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return None

def create_video(image_paths, output_video_name):
    """Creates a video from a list of image paths."""
    if not image_paths:
        print("No images to create video from.")
        return

    print(f"Preparing to create video: {output_video_name}")

    # Define the codec and create VideoWriter object
    # Using 'mp4v' for .mp4 files. Other options: 'XVID' for .avi
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(output_video_name, fourcc, FPS, (VIDEO_WIDTH, VIDEO_HEIGHT))

    if not video_writer.isOpened():
        print(f"Error: Could not open video writer for {output_video_name}")
        return

    total_images = len(image_paths)
    for i, image_path in enumerate(image_paths):
        filename_with_ext = os.path.basename(image_path)
        base_name = os.path.splitext(filename_with_ext)[0] # Filename without extension
        
        # Remove the prefix "Photo [number(s)] - "
        prefix_pattern = r"^Photo \d+\s*-\s*"
        cleaned_caption = re.sub(prefix_pattern, "", base_name)
        
        caption = cleaned_caption.strip()

        print(f"Processing image {i+1}/{total_images}: {filename_with_ext} with caption: '{caption}'")

        pil_image = add_caption_to_image(image_path, caption)
        if pil_image:
            # Convert PIL image to OpenCV format (RGB to BGR)
            frame = cv2.cvtColor(np.array(pil_image.convert('RGB')), cv2.COLOR_RGB2BGR)

            # Write the frame for the duration specified
            for _ in range(IMAGE_DURATION_SECONDS * FPS):
                video_writer.write(frame)
        else:
            print(f"Skipping image {image_path} due to processing error.")

    video_writer.release()
    print(f"Video '{output_video_name}' created successfully in current directory!")
 

# --- Main Execution ---
if __name__ == "__main__":
    # This import is needed for cv2.cvtColor with PIL Images
    import numpy as np


    # --- IMPORTANT: SET YOUR FOLDER PATH HERE ---
    # Example: '/content/drive/MyDrive/My Photos/Vacation2024'
    # Ensure this path is correct and exists in your Google Drive.
    photo_folder_path = input("Enter the full path to your photos folder in Google Drive (e.g., /content/drive/MyDrive/Photos): ")


    if os.path.exists(photo_folder_path):
        image_files = get_image_files(photo_folder_path)

        if image_files:
            random.shuffle(image_files) # Randomize the order
            print(f"Shuffled {len(image_files)} images.")
            create_video(image_files, VIDEO_FILENAME)
        else:
            print("No images found to process.")
    else:
        print(f"The specified folder path does not exist: {photo_folder_path}")
        print("Please verify the path and try again.")