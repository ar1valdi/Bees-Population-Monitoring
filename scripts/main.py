import cv2, os
import numpy as np
from ultralytics import YOLO
from choose_entry import choose_entry_box, draw_square, choose_multiple_entry_boxes
from count_in_box import read_file, check_for_bees_in_box
import time

movie = "2024_04_03__15_30_22"
extension = "mp4"

# get necessary paths
text_files_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'resources', 'text_files'))
movies_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'resources', 'movies', 'raw'))
movies_save_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'resources', 'movies', 'processed'))
models_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'resources', 'models'))


# creates a file with coordinates of bees based on a model
def save_boxes_to_file(results, movie_name):
    file_name = text_files_path + "/coords_" + movie_name + ".txt"
    file = open(file_name, "w")
    file.write(str(len(results)) + "\n")

    for i in range(len(results)):
        file.write(str(len(results[i].boxes)) + "\n")
        for j in range(len(results[i].boxes)):
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
            missing_idxs = np.setdiff1d(bees_in_box[i][1], prev_bees_idx)
            new_num = np.setdiff1d(outer_boxed_bees[i][1], missing_idxs).shape[0]
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


def get_entering_and_leaving_bees(entry_boxes, movie_name, quit_boxes):
    entering_bees = []
    leaving_bees = []

    for box in entry_boxes:
        boxed_bees, outer_boxed_bees = check_for_bees_in_box(box, read_file(f"{text_files_path}/coords_{movie_name}.txt"))
        bees_leaving_counter = count_entering_bees(boxed_bees, outer_boxed_bees, 20)
        entering_bees.append([boxed_bees, outer_boxed_bees, bees_leaving_counter])

    for box in quit_boxes:
        boxed_bees, outer_boxed_bees = check_for_bees_in_box(box, read_file(
            f"{text_files_path}/coords_{movie_name}.txt"))
        bees_leaving_counter = count_leaving_bees(boxed_bees, outer_boxed_bees, 20)
        leaving_bees.append([boxed_bees, outer_boxed_bees, bees_leaving_counter])

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
def save_to_csv(movie_path, path):
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


# performs full algorithm and shows movie preview
def run_algorithm(movie_name):
    entry_boxes = choose_multiple_entry_boxes(f"{movies_path}/{movie_name}.{extension}", frame_number=15)
    quit_boxes = choose_multiple_entry_boxes(f"{movies_path}/{movie_name}.{extension}", frame_number=15)

    # model training (uncomment for running model through video, not nessesery if coords txt was already generated)
    # model = YOLO(f"{models_path}/model3.pt")  # load a pretrained model (recommended for training)
    # results = model.track(source=f"{movies_path}/{movie_name}.{extension}",
    #               save=True,
    #               conf=0.4)  # predict on an image
    # save_boxes_to_file(results, movie_name)

    entering_bees, leaving_bees = get_entering_and_leaving_bees(entry_boxes, movie_name, quit_boxes)

    # saving a video with counter (1st one with counting bees in box and second for leaving bees)
    save_video_with_counter(f"{movie_name}.{extension}",
                            entering_bees,
                            leaving_bees, movies_path+'/',
                            movies_save_path+'/',
                            entry_boxes,
                            quit_boxes)
    # input = input()


def main():
    run_algorithm(movie)


if __name__ == "__main__":
    main()
