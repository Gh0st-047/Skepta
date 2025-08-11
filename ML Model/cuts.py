import cv2
import os

def split_image_3x3(image_path, output_dir="output"):
    # Read the image
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Could not read image: {image_path}")

    # Get dimensions
    height, width = img.shape[:2]
    cell_h = height // 3
    cell_w = width // 3

    # Create output folder
    os.makedirs(output_dir, exist_ok=True)

    count = 1
    for row in range(3):
        for col in range(3):
            x1, y1 = col * cell_w, row * cell_h
            x2, y2 = x1 + cell_w, y1 + cell_h
            cell = img[y1:y2, x1:x2]

            output_path = os.path.join(output_dir, f"cell_{count}.png")
            cv2.imwrite(output_path, cell)
            print(f"Saved {output_path}")
            count += 1

if __name__ == "__main__":
    split_image_3x3(r"E:\Projects\skepta\Skepta\body.png", "grid_cells")
