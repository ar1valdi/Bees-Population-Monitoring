import cv2
import time

movies_path = "../resources/movies/"


def read_file(file_path):
    with open(file_path, 'r') as file:
        num_keys = int(file.readline().strip())
        data = []
        for _ in range(num_keys):
            key = int(file.readline().strip())
            boxes = []
            for _ in range(key):
                box = list(map(float, file.readline().strip().split()))
                boxes.append(box)
            data.append(boxes)
    return data


def get_center(one_box) -> (float, float):
    return (one_box[0],one_box[1])


def is_point_in_box(box, center_point, offset=0):
    return (box[0] + offset < center_point[0] < box[2] - offset and box[1]-offset  > center_point[1] > box[3] + offset) or (box[0] + offset < center_point[0] < box[2] - offset and box[1]-offset  < center_point[1] < box[3] + offset)


# checks for number of bees from data (all frames) inside given box 
def check_for_bees_in_box(box, data):
    boxed_bees = []

    for key_data in data:
        bees_in_box = 0
        for one_box in key_data:
            center_point = get_center(one_box)
            if is_point_in_box(box,center_point):
                bees_in_box += 1

        # print(key_data)
        print("Bees is box:" + str(bees_in_box))
        boxed_bees.append(bees_in_box)

    return boxed_bees
