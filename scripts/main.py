import json

import cv2, os
import numpy as np
from ultralytics import YOLO
from choose_entry import choose_entry_box, draw_square, choose_multiple_entry_boxes
from count_in_box import read_file, check_for_bees_in_box
import time

movie = "2024_06_05__18_47_03"
extension = "mp4"

# get necessary paths
text_files_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'resources', 'text_files'))
movies_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'resources', 'movies', 'raw'))
movies_save_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'resources', 'movies', 'processed'))
models_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'resources', 'models'))
json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'resources', 'predicted_jsons'))


# creates a file with coordinates of bees based on a model
def save_boxes_to_file(results, movie_name):
    file_name = text_files_path + "/coords_" + movie_name + ".txt"
    file = open(file_name, "w")
    file.write(str(len(results)) + "\n")

    for i in range(len(results)):
        cnt = 0
        for n in results[i].boxes.cls:
            if n == 0:
                cnt += 1

        file.write(str(cnt) + "\n")
        for j in range(len(results[i].boxes)):
            if results[i].boxes.cls[j] != 0:
                continue
            x = float(results[i].boxes[j].xywh[0][0])
            y = float(results[i].boxes[j].xywh[0][1])
            w = float(results[i].boxes[j].xywh[0][2])
            h = float(results[i].boxes[j].xywh[0][3])
            if results[i].boxes[j].id is None:
                c = -1
            else:
                c = float(results[i].boxes[j].id)
            print(str(c) + str(" "))
            file.write(str(c) + " " + str(x) + " " + str(y) + " " + str(w) + " " + str(h) + "\n")

    file.close()


# count bees leaving the box
def count_leaving_bees(bees_in_box, outer_boxed_bees, max_delay=10):
    bees_leaving_counter = [0]
    prev_bees_cnt = 0
    prev_bees_idx = []
    prev_bees_idx_out = []
    delay = 0

    for i in range(1, len(bees_in_box)):
        new_num = 0
        delay -= 1

        if bees_in_box[i][0] > prev_bees_cnt and delay <= 0:
            new_idxs = np.setdiff1d(bees_in_box[i][1], prev_bees_idx)
            new_num = np.setdiff1d(new_idxs, prev_bees_idx_out).shape[0]
            if new_num > 0:
                delay = max_delay

        bees_leaving_counter.append(bees_leaving_counter[i-1] + new_num)

        prev_bees_cnt = bees_in_box[i][0]
        prev_bees_idx = bees_in_box[i][1]
        prev_bees_idx_out = outer_boxed_bees[i][1]

    return bees_leaving_counter


def count_entering_bees(bees_in_box, outer_boxed_bees, max_delay=10):
    bees_entering_counter = [0]
    prev_bees_cnt = 0
    prev_bees_idx = []
    delay = 0

    for i in range(1, len(bees_in_box)):
        new_num = 0
        delay -= 1

        if bees_in_box[i][0] < prev_bees_cnt and delay <= 0:
            missing_idxs = np.setdiff1d(prev_bees_idx, bees_in_box[i][1])
            new_num = np.setdiff1d(missing_idxs, outer_boxed_bees[i][1]).shape[0]
            if new_num > 0:
                delay = max_delay

        bees_entering_counter.append(bees_entering_counter[i - 1] + new_num)

        prev_bees_cnt = bees_in_box[i][0]
        prev_bees_idx = bees_in_box[i][1]

    return bees_entering_counter


def mark_entrance_sq_on_movie(entry_box, big_sq_offset, frame, color):
    draw_square([[entry_box[0], entry_box[1]], [entry_box[2], entry_box[3]]], frame, color)
    draw_square([[entry_box[0] - big_sq_offset, entry_box[1] - big_sq_offset],
             [entry_box[2] + big_sq_offset, entry_box[3] + big_sq_offset]], frame, color)


# save a video of counted bees with the counter
def save_video_with_counter(video_name, entering_bees, leaving_bees, path, path_out, entry_boxes, quit_boxes):
    video_capture = cv2.VideoCapture(path+video_name)
    frame_width = int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

    output_video = cv2.VideoWriter(str(path_out + 'counted_' + video_name), cv2.VideoWriter_fourcc(*'mp4v'), 30, (frame_width, frame_height))

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.5
    color = (255, 255, 255)
    thickness = 2
    big_sq_offset = 50

    i = 0
    play_slowdown = 30

    while True:
        ret, frame = video_capture.read()

        if not ret:
            break

        cnt = 0
        for j in range(len(entering_bees)):
            cv2.putText(frame, "inbox___" + str(j) + ":" + str(entering_bees[j][0][i][0]),
                        (350, 40 * (1 + 2*j)), font, font_scale, color, thickness)
            cv2.putText(frame, "cnt_in_" + str(j) + ": " + str(entering_bees[j][2][i]),
                        (350, 40 * (2 + 2*j)), font, font_scale, color, thickness)
            cnt += entering_bees[j][2][i]
        for j in range(len(leaving_bees)):
            cv2.putText(frame, "inbox___" + str(j) + ":" + str(leaving_bees[j][0][i][0]),
                        (20, 40 * (1 + 2*j)), font, font_scale, color, thickness)
            cv2.putText(frame, "cnt_out_" + str(j) + ": " + str(leaving_bees[j][2][i]),
                        (20, 40 * (2 + 2*j)), font, font_scale, color, thickness)
            cnt -= leaving_bees[j][2][i]
        i += 1

        cv2.putText(frame, f"delta: {cnt}", (frame_width - 400, frame_height - 40), font, font_scale, color, thickness)

        for box in quit_boxes:
            mark_entrance_sq_on_movie(box, big_sq_offset, frame, (0, 0, 255))
        for box in entry_boxes:
            mark_entrance_sq_on_movie(box, big_sq_offset, frame, (0, 255, 0))

        output_video.write(frame)
        cv2.imshow('Frame', frame)

        key = cv2.waitKey(play_slowdown) & 0xFF

        if key == ord('q'):
            break
        elif key == ord('a'):
            play_slowdown += 30
        elif key == ord('a'):
            play_slowdown += 10
        elif key == ord('d') and play_slowdown > 10:
            play_slowdown -= 10
        elif key == ord('f') and play_slowdown > 30:
            play_slowdown -= 30

    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    video_capture.release()
    output_video.release()
    cv2.destroyAllWindows()


def sort_boxes_by_x_pos(entering_bees, leaving_bees):
    m_entering_bees = sorted(entering_bees, key=lambda x: x[3])
    m_leaving_bees = sorted(leaving_bees, key=lambda x: x[3])

    iter_e, iter_l = 0, 0
    for i in range(len(m_entering_bees) + len(m_leaving_bees)):
        if iter_e >= len(m_entering_bees):
            m_leaving_bees[iter_l][3] = i
            iter_l += 1
            continue

        if iter_l >= len(m_leaving_bees):
            m_entering_bees[iter_e][3] = i
            iter_e += 1
            continue

        if m_entering_bees[iter_e][3] < m_leaving_bees[iter_l][3]:
            m_entering_bees[iter_e][3] = i
            iter_e += 1
        else:
            m_leaving_bees[iter_l][3] = i
            iter_l += 1

    return m_entering_bees, m_leaving_bees


def get_entering_and_leaving_bees(entry_boxes, movie_name, quit_boxes):
    entering_bees = []
    leaving_bees = []

    for box in entry_boxes:
        boxed_bees, outer_boxed_bees = check_for_bees_in_box(box, read_file(f"{text_files_path}/coords_{movie_name}.txt"))
        bees_leaving_counter = count_entering_bees(boxed_bees, outer_boxed_bees)
        entering_bees.append([boxed_bees, outer_boxed_bees, bees_leaving_counter, box[0]])

    for box in quit_boxes:
        boxed_bees, outer_boxed_bees = check_for_bees_in_box(box, read_file(
            f"{text_files_path}/coords_{movie_name}.txt"))
        bees_leaving_counter = count_leaving_bees(boxed_bees, outer_boxed_bees)
        leaving_bees.append([boxed_bees, outer_boxed_bees, bees_leaving_counter, box[0]])

    entering_bees, leaving_bees = sort_boxes_by_x_pos(entering_bees, leaving_bees)
    return entering_bees, leaving_bees


def save_results_csv(entering_bees, leaving_bees, path, movie_name):
    line = movie_name + str('.') + extension
    for i in range(len(entering_bees)):
        line = line + str(';') + str(entering_bees[i][2][-1])
    for i in range(2 - len(entering_bees)):
        line = line + str(';') + "-1"
    for i in range(len(leaving_bees)):
        line = line + str(';') + str(leaving_bees[i][2][-1])
    for i in range(2 - len(leaving_bees)):
        line = line + str(';') + "-1"
    line = line + '\n'

    with open(path, "a") as f:
        f.write(line)


# runs algorithm from premade .txt files and adds it to .csv file
def run_test_to_csv(movie_path, path):
    entry_boxes = choose_multiple_entry_boxes(f"{movies_path}/{movie_path}.{extension}", frame_number=15)
    quit_boxes = choose_multiple_entry_boxes(f"{movies_path}/{movie_path}.{extension}", frame_number=15)

    entering_bees, leaving_bees = get_entering_and_leaving_bees(entry_boxes, movie_path, quit_boxes)
    save_results_csv(entering_bees, leaving_bees, path, movie_path)


def get_filenames_without_extension(folder_path):
    filenames_without_extension = []
    for filename in os.listdir(folder_path):
        if os.path.isfile(os.path.join(folder_path, filename)):
            filenames_without_extension.append(os.path.splitext(filename)[0])
    return filenames_without_extension


def convert_hills_to_peaks(data: np.array(int) or np.array(float)):
    non_zero_indices = np.where(data != 0)[0]

    if len(non_zero_indices) == 0:
        return data.astype(np.int8).tolist()

    output = np.zeros_like(data)

    hill_start = non_zero_indices[0]

    for i in range(1, len(non_zero_indices)):
        if non_zero_indices[i] != non_zero_indices[i - 1] + 1:
            hill_end = non_zero_indices[i - 1]
            peak_index = hill_start + np.argmax(data[hill_start:hill_end + 1])
            output[peak_index] = 1
            hill_start = non_zero_indices[i]

    hill_end = non_zero_indices[-1]
    peak_index = hill_start + np.argmax(data[hill_start:hill_end + 1])
    output[peak_index] = 1

    return output.astype(np.int8).tolist()


def save_data_to_json_for_nn(entering_bees, leaving_bees, json_path):
    combined_data = entering_bees + leaving_bees
    combined_data = sorted(combined_data, key=lambda x: x[3])

    peaks = {}
    for data in combined_data:
        peaks[data[3]] = get_peaks_from_counts(data[2])

    with open(json_path, 'w') as json_file:
        json.dump({"peaks": peaks}, json_file, indent=4)


def get_peaks_from_counts(passing_counter):
    before_scaling = np.diff(passing_counter)
    original_indices = np.linspace(0, len(before_scaling) - 1, num=len(before_scaling))
    new_indices = np.linspace(0, len(before_scaling) - 1, num=5000)

    scaled_array = np.interp(new_indices, original_indices, before_scaling)
    return convert_hills_to_peaks(scaled_array)


# performs full algorithm and shows movie preview
def run_algorithm(movie_name, create_txt=False):
    entry_boxes = choose_multiple_entry_boxes(f"{movies_path}/{movie_name}.{extension}", frame_number=15)
    quit_boxes = choose_multiple_entry_boxes(f"{movies_path}/{movie_name}.{extension}", frame_number=15)

    # actual tracking (uncomment for running model through video, not nessesery if coords txt was already generated)
    if create_txt:
        model = YOLO(f"{models_path}/new_angle_30.pt")
        results = model.track(source=f"{movies_path}/{movie_name}.{extension}",
                      save=True,
                      show=False,
                      conf=0.4)
        save_boxes_to_file(results, movie_name)

    entering_bees, leaving_bees = get_entering_and_leaving_bees(entry_boxes, movie_name, quit_boxes)

    # saving a video with counter (1st one with counting bees in box and second for leaving bees)
    save_video_with_counter(f"{movie_name}.{extension}",
                            entering_bees,
                            leaving_bees, movies_path+'/',
                            movies_save_path+'/',
                            entry_boxes,
                            quit_boxes)


def run_preparing_data_for_nn(movie_name, save_path, create_txt=False):
    entry_boxes = choose_multiple_entry_boxes(f"{movies_path}/{movie_name}.{extension}", frame_number=15)
    quit_boxes = choose_multiple_entry_boxes(f"{movies_path}/{movie_name}.{extension}", frame_number=15)

    # actual tracking (uncomment for running model through video, not nessesery if coords txt was already generated)
    if create_txt:
        model = YOLO(f"{models_path}/szymanski_and_splendid_side_100_front_30.pt")
        results = model.track(source=f"{movies_path}/{movie_name}.{extension}",
                              save=True,
                              show=False,
                              conf=0.4)
        save_boxes_to_file(results, movie_name)

    entering_bees, leaving_bees = get_entering_and_leaving_bees(entry_boxes, movie_name, quit_boxes)
    save_data_to_json_for_nn(entering_bees, leaving_bees, save_path)


def main():
    # run_preparing_data_for_nn(movie, json_path + "/" + movie + ".json")
    run_algorithm(movie, False)


if __name__ == "__main__":
    main()
