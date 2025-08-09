# import easyocr
# import re
# import cv2
# import numpy as np
# import os
# from pathlib import Path

# os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# # Initialize EasyOCR once
# reader = easyocr.Reader(['en'], gpu=False)

# # Confidence threshold
# CONFIDENCE_THRESHOLD = 0.95

# def method_1_simple_easyocr(image):
#     results = reader.readtext(image)
#     return filter_digits(results), results

# def method_2_remove_light_background(image):
#     hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
#     light_bg_mask = cv2.inRange(hsv, (0, 0, 180), (180, 60, 255))
#     digits_mask = cv2.bitwise_not(light_bg_mask)

#     kernel = np.ones((2, 2), np.uint8)
#     digits_mask = cv2.morphologyEx(digits_mask, cv2.MORPH_OPEN, kernel)
#     digits_mask = cv2.morphologyEx(digits_mask, cv2.MORPH_CLOSE, kernel)

#     processed = cv2.bitwise_not(digits_mask)
#     results = reader.readtext(processed)
#     return filter_digits(results), results

# def method_3_adjust_saturation_brightness(image):
#     hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
#     h, s, v = cv2.split(hsv)

#     light_mask = cv2.inRange(hsv, (0, 0, 200), (180, 60, 255))
#     v = np.where(light_mask == 255, v * 0.4, v)
#     s = np.where(light_mask == 0, np.clip(s * 1.8, 0, 255), s)

#     adjusted_hsv = cv2.merge([h, s.astype(np.uint8), v.astype(np.uint8)])
#     adjusted_bgr = cv2.cvtColor(adjusted_hsv, cv2.COLOR_HSV2BGR)
#     gray = cv2.cvtColor(adjusted_bgr, cv2.COLOR_BGR2GRAY)

#     clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
#     enhanced = clahe.apply(gray)
#     results = reader.readtext(enhanced)
#     return filter_digits(results), results

# def filter_digits(results):
#     return [(text, prob) for (bbox, text, prob) in results if re.fullmatch(r'\d+(\.\d+)?', text) and prob >= CONFIDENCE_THRESHOLD]

# def process_image(image_path):
#     image = cv2.imread(str(image_path))
#     methods = [
#         ("Simple EasyOCR", method_1_simple_easyocr),
#         ("Remove Light Background", method_2_remove_light_background),
#         ("Saturation & Brightness Adjust", method_3_adjust_saturation_brightness)
#     ]

#     best_candidate = None  # (text, prob)

#     for method_name, method in methods:
#         try:
#             print(f"  Trying method: {method_name}")
#             valid_results, all_results = method(image)

#             if valid_results:
#                 print(f"  ✅ Success with {method_name}")
#                 return [text for (text, prob) in valid_results]

#             for (bbox, text, prob) in all_results:
#                 if re.fullmatch(r'\d+(\.\d+)?', text):
#                     if best_candidate is None or prob > best_candidate[1]:
#                         best_candidate = (text, prob)

#         except Exception as e:
#             print(f"  ⚠️ Error in {method_name}: {e}")

#     if best_candidate:
#         print(f"  ⚠️ Using fallback (best below threshold: {best_candidate[1]:.2f})")
#         return [best_candidate[0]]

#     print("  ❌ No numbers detected.")
#     return []


# def run_on_folder(folder_path="split_cells"):
#     folder = Path(folder_path)
#     image_paths = sorted(folder.glob("*.[pjPJ]*[npNP]*[gG]"))  # matches .png, .jpg, .jpeg etc.

#     for img_path in image_paths:
#         print(f"\n📄 Image: {img_path.name}")
#         numbers = process_image(img_path)
#         if numbers:
#             print("  ➜ Numbers found:", ', '.join(numbers))
#         else:
#             print("  ➜ No numbers found.")

# # Run the pipeline
# run_on_folder("split_cells")











# import easyocr
# import re
# import os
# import cv2
# import numpy as np


# # Load the full image
# image_path = r"E:\Projects\skepta\Skepta\ML Model\captcha.png"
# image = cv2.imread(image_path)

# # Set number of rows and columns (for 9 cells, 3x3)
# rows, cols = 3, 3
# height, width = image.shape[:2]
# cell_h, cell_w = height // rows, width // cols

# # Initialize OCR reader
# reader = easyocr.Reader(['en'], gpu=False)

# # Loop over cells
# for row in range(rows):
#     for col in range(cols):
#         idx = row * cols + col + 1
#         x1, y1 = col * cell_w, row * cell_h
#         x2, y2 = x1 + cell_w, y1 + cell_h
#         cell = image[y1:y2, x1:x2]

#         # OCR on the cell
#         results = reader.readtext(cell)

#         # Extract numeric results
#         numbers_only = [
#             (text, prob)
#             for (bbox, text, prob) in results
#             if re.fullmatch(r'\d+(\.\d+)?', text)
#         ]

#         print(f"📦 Region {idx}:")
#         if numbers_only:
#             for num, prob in numbers_only:
#                 print(f"  ➜ Number: {num} (Confidence: {prob:.2f})")
#         else:
#             print("  ❌ No numeric text detected.\n")












import easyocr
import re
import cv2
import numpy as np

# Load image
image_path = r"E:\Projects\skepta\Skepta\ML Model\captcha.png"
image = cv2.imread(image_path)

# Initialize OCR
reader = easyocr.Reader(['en'], gpu=False)

# --- Step 1: Detect target number ---
# Detect only from top strip of the image (full width, small height)
header_h = int(image.shape[0] * 0.12)  # small strip at top
header_img = image[:header_h, :]

header_results = reader.readtext(header_img)
target_number = None
for (_, text, _) in header_results:
    match = re.search(r'\b\d+\b', text)
    if match:
        target_number = match.group()
        break

print(f"🎯 Target number: {target_number}")

# --- Step 2: Split into 3x3 grid like your original code ---
rows, cols = 3, 3
height, width = image.shape[:2]
cell_h, cell_w = height // rows, width // cols

for row in range(rows):
    for col in range(cols):
        idx = row * cols + col + 1
        x1, y1 = col * cell_w, row * cell_h
        x2, y2 = x1 + cell_w, y1 + cell_h
        cell = image[y1:y2, x1:x2]

        results = reader.readtext(cell)

        numbers_only = [
            (text, prob)
            for (bbox, text, prob) in results
            if re.fullmatch(r'\d+(\.\d+)?', text)
        ]

        print(f"📦 Region {idx}:")
        if numbers_only:
            for num, prob in numbers_only:
                print(f"  ➜ Number: {num} (Confidence: {prob:.2f})")
        else:
            print("  ❌ No numeric text detected.\n")
