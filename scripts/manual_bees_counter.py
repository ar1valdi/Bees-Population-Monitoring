import json
import os

import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog

fps = 60
frame_count = 0
video_duration = 0
original_frames = 0
click_times = []
started = False
paused = True
selected_number = 0
file_path = None


def set_stats():
    global fps, video_duration, original_frames
    original_frames = cap.get(cv2.CAP_PROP_FPS)
    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    video_duration = total_frames / original_frames

    print(f"Original Video FPS: {fps}")
    print(f"Total frames: {total_frames}")
    print(f"Video duration (seconds): {video_duration}")

def select_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(filetypes=[("MP4 files", "*.mp4")],initialdir="../resources/movies")
    root.destroy()
    return file_path


def mark_time(event, x, y, flags, param):
    global started, paused
    if event == cv2.EVENT_LBUTTONDOWN:
        if not started:
            started = True
            paused = False
            return

        current_time = frame_count / original_frames
        index = int((current_time / video_duration) * 5000)
        if 0 <= index < 5000:
            array[index] = 1
            click_times.append(current_time)
            print(f"Marked at time: {current_time:.2f}s, Index: {index}")

    if event == cv2.EVENT_RBUTTONDOWN:
        current_time = frame_count / original_frames
        index = int((current_time / video_duration) * 5000)

        for i in range(index, -1, -1):
            if array[i] == 1:
                array[i] = 0
                click_times.pop()
                print(f"index {i} reverted to 0")
                break


def get_user_input():
    global selected_number, cap

    ret, frame = cap.read()
    if ret:
        cv2.imshow('Video', frame)

    root = tk.Tk()
    root.title("Select a Number")

    root.wm_attributes('-topmost', True)

    def submit():
        global selected_number
        selected_number = int(entry.get())
        root.destroy()

    label = tk.Label(root, text="Enter a number from 0 to 3:")
    label.pack()

    entry = tk.Entry(root)
    entry.pack()

    entry.focus_set()

    button = tk.Button(root, text="Submit", command=submit)
    button.pack()

    root.mainloop()


def play_video():
    global fps, frame_count, paused
    left_arrow = 0x250000
    right_arrow = 0x270000
    fps_change = 5

    while cap.isOpened():
        if not paused:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            cv2.imshow('Video', frame)

        key = cv2.waitKey(int(1000 / fps)) & 0xFF
        if key == ord('q'):
            exit(3)
        elif key == ord(' '):
            paused = not paused
        elif key == ord('a') or key == left_arrow:
            if frame_count - int(fps) >= 0:
                frame_count -= int(fps)
            else:
                frame_count = 0
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
        elif key == ord('d') or key == right_arrow:
            frame_count += int(fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
        elif key == ord('s'):
            if fps > fps_change:
                fps -= fps_change
        elif key == ord('w'):
            if fps < 120:
                fps += fps_change

    cap.release()
    cv2.destroyAllWindows()


def save_to_json(selected_number, array):
    global video_path
    file_name = os.path.splitext(os.path.basename(video_path))[0]
    output_file = "marked_jsons/" + file_name + ".json"

    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            peaks_data = json.load(f)
        peaks = peaks_data.get("peaks", {})
    else:
        peaks = {}

    peaks[str(selected_number)] = [value for index, value in enumerate(array)]

    with open(output_file, 'w') as f:
        json.dump({"peaks": peaks}, f, indent=4)

    print(f"Array saved to {output_file}")


array = [0] * 5000

video_path = select_file()
if not video_path:
    print("No file selected.")
    exit()

# Load the video file
cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    print("Error: Could not open video.")
    exit()

set_stats()

cv2.namedWindow('Video')
cv2.setWindowProperty('Video', cv2.WND_PROP_TOPMOST, 1)

get_user_input()
cv2.setMouseCallback('Video', mark_time)
play_video()

print("Click times (seconds): ", click_times)
print("Array: ", array)
print("At entry: ", selected_number)

save_to_json(selected_number, array)
