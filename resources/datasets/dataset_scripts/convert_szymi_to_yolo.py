import fileinput
import os


def convert():
    info = "info.txt"
    out_dir = "labels"

    with open(info, 'r') as f:
        lines = f.read().splitlines()

    data = []
    for line in lines:
        split = line.split(' ', 2)
        data.append(split)

    for d in data:
        filename = d[0].replace(".jpg", ".txt")
        nums = d[2].split(" ")
        with open(out_dir + "/" + filename, 'w') as f:
            for i in range(int(d[1])):
                l = "0"
                x, y, w, h = int(nums[i*4+0]) / 416, int(nums[i*4+1]) / 416, int(nums[i*4+2]) / 416, int(nums[i*4+3]) / 416
                l += " " + str(x + 0.5*w)
                l += " " + str(y + 0.5*h)
                l += " " + str(w)
                l += " " + str(h)
                l += "\n"
                f.write(l)


convert()
