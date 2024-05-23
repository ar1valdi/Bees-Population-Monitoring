import cv2, os
from ultralytics import YOLO
from choose_entry import choose_entry_box, draw_square
from count_in_box import read_file, check_for_bees_in_box

# get necessary paths
text_files_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'resources', 'text_files'))
movies_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'resources', 'movies'))
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
            file.write(str(x) + " " + str(y) + " " + str(w) + " " + str(h) + "\n")

    file.close()


# count bees leaving the box
def count_leaving_bees(bees_in_box, max_delay=10):
    bees_leaving_counter = [0]
    delay = 0

    for i in range(1, len(bees_in_box)):
        if bees_in_box[i] > bees_in_box[i-1] and delay <= 0:
            bees_leaving_counter.append(bees_leaving_counter[i-1] + 1)
            delay = max_delay
        else:
            bees_leaving_counter.append(bees_leaving_counter[i-1])
            delay -= 1
    
    return bees_leaving_counter


# save a video of counted bees with the counter
def save_video_with_counter(video_name, boxed_bees, counted_bees, path, entry_box):
    video_capture = cv2.VideoCapture(path+video_name)
    frame_width = int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

    output_video = cv2.VideoWriter(str(path + 'counted_' + video_name), cv2.VideoWriter_fourcc(*'mp4v'), 30, (frame_width, frame_height))

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.5
    color = (255, 255, 255)
    thickness = 2

    i = 0

    while True:
        ret, frame = video_capture.read()

        if not ret:
            break

        cv2.putText(frame, "inbox: " + str(boxed_bees[i]), (20, frame_height - 20), font, font_scale, color, thickness)
        cv2.putText(frame, "cnt: " + str(counted_bees[i]), (frame_width - 170, frame_height - 20), font, font_scale, color, thickness)
        i += 1

        draw_square([[entry_box[0], entry_box[1]], [entry_box[2], entry_box[3]]], frame)
        output_video.write(frame)
        cv2.imshow('Frame', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    output_video.release()
    cv2.destroyAllWindows()


def main():
    movie_name = "dif_angle"
    extension = "mp4"

    entry_box = choose_entry_box(f"{movies_path}/{movie_name}.{extension}", frame_number=15)

    # model training (uncomment for training a new model)
    model = YOLO(f"{models_path}/model3.pt")  # load a pretrained model (recommended for training)
    results = model(source=f"{movies_path}/{movie_name}.{extension}", save=False, conf=0.4)  # predict on an image
    save_boxes_to_file(results, movie_name)

    boxed_bees = check_for_bees_in_box(entry_box, read_file(f"{text_files_path}/coords_{movie_name}.txt"))
    bees_leaving_counter = count_leaving_bees(boxed_bees, max_delay=20)

    # saving a video with counter (1st one with counting bees in box and second for leaving bees)
    save_video_with_counter(f"{movie_name}.{extension}", boxed_bees, bees_leaving_counter, movies_path+'/', entry_box)
    # input = input()


if __name__ == "__main__":
    main()