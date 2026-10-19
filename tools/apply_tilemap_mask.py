import os
import numpy as np
import cv2
from PIL import Image

input_mask = "data/tilemap_template.png"
tile_image = "data/tile.png"
output_image_path = "data/output.png"
os.makedirs(os.path.dirname(output_image_path), exist_ok=True)

mask = cv2.imread(input_mask, cv2.IMREAD_UNCHANGED)
tile = cv2.imread(tile_image, cv2.IMREAD_UNCHANGED)
output_image = np.zeros_like(mask)

for i in range(0, mask.shape[0], tile.shape[0]):
	for j in range(0, mask.shape[1], tile.shape[1]):
		output_image[i:i+tile.shape[0], j:j+tile.shape[1]] = tile

output_image[mask[:, :, 3] == 0] = np.array([0, 0, 0, 0])

cv2.imwrite(output_image_path, output_image)