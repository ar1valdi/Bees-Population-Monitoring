from ultralytics import YOLO
import torch

model_src = "resources/models/model3.pt"


def set_class_probability(model_path: str, class_name: str, value: float):
    model = YOLO(model_src)
    print(model)


set_class_probability(model_src, "0", 0)

# model = YOLO("model3.pt")

# result = model(source=src, show=True, conf=0.4)
