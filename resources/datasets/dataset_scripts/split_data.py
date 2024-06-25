import os
import random
import shutil


def split_dataset(labels_folder, images_folder, output_folder):
    # Get the list of label files and image files
    label_files = [file for file in os.listdir(labels_folder) if file.endswith('.txt')]
    image_files = [file for file in os.listdir(images_folder) if file.endswith('.jpg')]

    # Shuffle the lists to randomize the order
    random.shuffle(label_files)

    # Calculate the sizes of train, validation, and test sets
    total_samples = len(label_files)
    train_size = int(total_samples * 0.8)
    val_size = int(total_samples * 0.1)
    test_size = total_samples - train_size - val_size

    # Divide the list into train, validation, and test sets
    train_labels = label_files[:train_size]
    val_labels = label_files[train_size:train_size + val_size]
    test_labels = label_files[train_size + val_size:]

    # Create directories for train, validation, and test sets
    for set_name in ['train', 'val', 'test']:
        set_folder = os.path.join(output_folder, set_name)
        os.makedirs(os.path.join(set_folder, 'labels'), exist_ok=True)
        os.makedirs(os.path.join(set_folder, 'img'), exist_ok=True)

    # Move label files and corresponding image files to their respective directories
    for label_file in train_labels:
        image_file = label_file.replace('.txt', '.jpg')
        shutil.move(os.path.join(labels_folder, label_file), os.path.join(output_folder, 'train', 'labels', label_file))
        shutil.move(os.path.join(images_folder, image_file), os.path.join(output_folder, 'train', 'img', image_file))

    for label_file in val_labels:
        image_file = label_file.replace('.txt', '.jpg')
        shutil.move(os.path.join(labels_folder, label_file), os.path.join(output_folder, 'val', 'labels', label_file))
        shutil.move(os.path.join(images_folder, image_file), os.path.join(output_folder, 'val', 'img', image_file))

    for label_file in test_labels:
        image_file = label_file.replace('.txt', '.jpg')
        shutil.move(os.path.join(labels_folder, label_file), os.path.join(output_folder, 'test', 'labels', label_file))
        shutil.move(os.path.join(images_folder, image_file), os.path.join(output_folder, 'test', 'img', image_file))


labels_folder = 'labels'
images_folder = 'train_set'
output_folder = 'out/bees_ver_3'
split_dataset(labels_folder, images_folder, output_folder)
print("Dataset split into train, val, and test sets.")