# -*- coding: utf-8 -*-
"""
Author -- Andreas Schörgenhumer

################################################################################

The following copyright statement applies to all code within this file.

Copyright statement:
This material, no matter whether in printed or electronic form, may be used for
personal and non-commercial educational use only. Any reproduction of this
manuscript, no matter whether as a whole or in parts, no matter whether in
printed or in electronic form, requires explicit prior acceptance of the
authors.

################################################################################

This script will take a folder INPUT_DIR and reduce the image size of all .jpg
images via two heuristics until the new image size is equal to or smaller than
MAX_FILE_SIZE (bytes). Heuristic 1 is about repeatedly reducing the image
quality until MIN_QUALITY is reached. If the image size is still too big,
heuristic 2 is applied, where the resolution is repeatedly reduced. The
resulting image files will be written to the folder OUTPUT_DIR. See the help
info text of the individual arguments for default values and further details.

Usage: python reduce_image_sizes.py INPUT_DIR
            [--output_dir OUTPUT_DIR]
            [--max_file_size MAX_FILE_SIZE]
            [--min_quality MIN_QUALITY]
            [--resize_quality RESIZE_QUALITY]
"""

import argparse
import os
import shutil
import warnings

from PIL import Image
from tqdm import tqdm

parser = argparse.ArgumentParser()
parser.add_argument("input_dir", type=str, help="The directory containing the images.")
parser.add_argument("--output_dir", type=str,
                    help="The directory containing the resized images. If not specified, the original 'input_dir' with "
                         "the additional postfix '_resized' will be used (directory will be created).")
parser.add_argument("--max_file_size", type=int, default=250_000,
                    help="Maximum allowed size in bytes up to which images are not resized. Default: 250kB")
parser.add_argument("--min_quality", type=int, default=70,
                    help="The minimum image quality when continuously reducing the quality to obtain smaller file "
                         "sizes (heuristic 1). Default: 70")
parser.add_argument("--resize_quality", type=int, default=95,
                    help="The image quality when storing resized images (heuristic 2). Default: 95")
args = parser.parse_args()

input_dir = args.input_dir
if not os.path.isdir(input_dir):
    raise ValueError(f"'{input_dir}' must be an existing directory")
output_dir = args.output_dir if args.output_dir is not None else input_dir + "_resized"
os.makedirs(output_dir, exist_ok=True)
supported_extensions = {".jpg", ".JPG", ".jpeg", ".JPEG"}
image_files = [f.path for f in os.scandir(input_dir) if f.is_file() and os.path.splitext(f)[1] in supported_extensions]

for i, image_file in tqdm(enumerate(image_files), total=len(image_files)):
    file_name = os.path.basename(image_file)
    file_size = os.path.getsize(image_file)
    
    if file_size > args.max_file_size:
        # Start from 95% of the original image quality and resolution and reduce by 5% after each iteration
        quality = 95
        resize_factor = 0.95
        new_file_size = file_size
        new_image_file = os.path.join(output_dir, file_name)
        
        while new_file_size > args.max_file_size:
            with Image.open(image_file) as image:
                # Heuristic 1: Try to save the image with reduced quality (until some minimum is reached)
                if quality >= args.min_quality:
                    image.save(new_image_file, quality=quality)
                    quality -= 5
                # Heuristic 2: If reducing the quality still leads to too big image sizes, try reducing the resolution
                else:
                    if resize_factor <= 0:
                        warnings.warn(f"resize_factor <= 0, could not reduce image size of '{image_file}'")
                        os.remove(new_image_file)
                        break
                    new_width, new_height = int(image.width * resize_factor), int(image.height * resize_factor)
                    new_image = image.resize((new_width, new_height))
                    new_image.save(new_image_file, quality=args.resize_quality)
                    resize_factor -= 0.05
            new_file_size = os.path.getsize(new_image_file)
    else:
        shutil.copy(image_file, os.path.join(output_dir, file_name))
