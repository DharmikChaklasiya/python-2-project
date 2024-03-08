import os
import csv
import shutil
from PIL import Image
import hashlib
import argparse


def validate_images(
    input_dir: str, output_dir: str, log_file: str, formatter: str = "07d"
):
    # Validate input directory
    if not os.path.isdir(input_dir):
        raise ValueError("input_dir is not an existing directory")

    # Prepare output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Prepare log file and its directory
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, "w") as log:
        pass  # Just creating/resetting the log file

    valid_images_count = 0
    hashed_images = set()

    # Prepare labels CSV file
    labels_csv_path = os.path.join(output_dir, "labels.csv")
    with open(labels_csv_path, "w", newline="") as csvfile:
        fieldnames = ["name", "label"]
        writer = csv.DictWriter(csvfile, delimiter=";", fieldnames=fieldnames)
        writer.writeheader()

        for root, _, files in os.walk(input_dir):
            files.sort(key=lambda f: os.path.abspath(os.path.join(root, f)))
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, start=input_dir)
                try:
                    # Rule 1: Check file extension
                    if not file.lower().endswith((".jpg", ".jpeg")):
                        raise ValueError("Invalid file extension")

                    # Rule 2: Check file size
                    if os.path.getsize(file_path) > 250000:
                        raise ValueError("File size exceeds limit")

                    # Open image to check further rules
                    with Image.open(file_path) as image:
                        # Rule 3: Validate image can be read
                        # Rule 4: Check image shape
                        if image.mode not in ["RGB", "L"]:
                            raise ValueError("Invalid image mode")
                        if image.size[0] < 100 or image.size[1] < 100:
                            raise ValueError("Image size is too small")

                        # Rule 5: Check variance
                        pixels = list(image.getdata())
                        if len(set(pixels)) == 1:
                            raise ValueError("Image has low variance")

                        # Rule 6: Check if image has been copied already
                        image_hash = hashlib.sha256(image.tobytes()).hexdigest()
                        if image_hash in hashed_images:
                            raise ValueError("Image has already been copied")
                        hashed_images.add(image_hash)

                        # Copy valid image
                        output_filename = f"{format(valid_images_count, formatter)}.jpg"
                        output_path = os.path.join(output_dir, output_filename)
                        shutil.copy(file_path, output_path)

                        # Write label to CSV
                        label = "".join(
                            [char for char in file.split(".")[0] if char.isalpha()]
                        ).lower()
                        writer.writerow({"name": output_filename, "label": label})

                        valid_images_count += 1

                except ValueError as error:
                    # Log invalid files
                    with open(log_file, "a") as log:
                        log.write(f"{rel_path},{str(error)}\n")

    return valid_images_count


if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser(description="Validate and process images.")

    # Add an argument for the input directory
    parser.add_argument(
        "input_dir", type=str, help="The input directory where images are located."
    )

    # Optionally, you could add arguments for output_dir and log_file
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./validated_pictures",
        help="The output directory for valid images.",
    )
    parser.add_argument(
        "--log_file",
        type=str,
        default="./validation_log.txt",
        help="The log file path for recording invalid files.",
    )

    # Parse the arguments
    args = parser.parse_args()

    # Call the function with arguments from the command line
    copied_files_count = validate_images(args.input_dir, args.output_dir, args.log_file)
    print(f"Number of valid files copied: {copied_files_count}")
