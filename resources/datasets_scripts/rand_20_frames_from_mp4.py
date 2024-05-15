import os
import random
import imageio
from moviepy.editor import VideoFileClip


def extract_frames(video_path, output_folder, num_frames=20):
    # Open the video file
    clip = VideoFileClip(video_path)

    # Get total number of frames
    total_frames = int(clip.duration * clip.fps)

    # Choose random frames
    random_frames = random.sample(range(total_frames), num_frames)

    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Extract and save frames
    for i, frame_num in enumerate(random_frames):
        frame = clip.get_frame(frame_num / clip.fps)
        filename = f"{os.path.splitext(os.path.basename(video_path))[0]}_{frame_num}.jpg"
        frame_path = os.path.join(output_folder, filename)
        imageio.imwrite(frame_path, frame)
        print(f"Saved frame {frame_num}/{total_frames} as {filename}")


# Example usage:
video_file = "example.mp4"  # Change this to your MP4 file path
output_folder = "frames"  # Output folder name

extract_frames(video_file, output_folder)
