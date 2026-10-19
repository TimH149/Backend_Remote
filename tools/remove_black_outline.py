import os
import numpy as np
import cv2
from PIL import Image

input_path = "C:\\Users\\Milan\\Documents\\spoken-grammar-repair\\Assets\\Sprites\\Trash\\trash"
output_path = "C:\\Users\\Milan\\Documents\\spoken-grammar-repair\\Assets\\Sprites\\Trash\\trash_no_outline"

os.makedirs(output_path, exist_ok=True)

allowed_filetypes = [".png"]

def enlarge(image, scale_factor=8):
    height, width = image.shape[:2]
    new_height, new_width = int(height * scale_factor), int(width * scale_factor)
    enlarged_image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_NEAREST)
    return enlarged_image

def remove_black_outline(image):
    # Create a mask for transparent pixels
    transparent_mask = image[:, :, 3] == 0  # Assuming the image has an alpha channel
    # add one pixel to each side of the transparent mask
    transparent_mask = np.pad(array=transparent_mask, pad_width=1, mode='constant', constant_values=1)

    black_mask = np.all(image[:, :, :3] < 50, axis=2)

    # cv2.imshow("Transparent Mask", enlarge(black_mask.astype(np.uint8) * 255))
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    kernel = np.ones((3, 3), np.uint8)
    transparent_mask_plusone = cv2.dilate(transparent_mask.astype(np.uint8), kernel, iterations=1)

    transparent_mask_smaller = transparent_mask_plusone[1:-1, 1:-1]

    # set black pixels in the mask to transparent
    image[(transparent_mask_smaller == 1) & black_mask] = [0, 0, 0, 0]

    return image

for filename in os.listdir(input_path):
    if any(filename.endswith(ext) for ext in allowed_filetypes):
        input_file = os.path.join(input_path, filename)
        output_file = os.path.join(output_path, filename)

        # Load the image
        image = np.array(Image.open(input_file))

        # Remove the black outline
        image_no_outline = remove_black_outline(image)

        # Save the modified image
        Image.fromarray(image_no_outline).save(output_file)

		