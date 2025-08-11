# # from PIL import Image

# # # === Settings ===
# # input_path = "captcha.png"          # Original image
# # output_path = "captcha_cropped.png" # Cropped image

# # top_percent = 0.20     # Remove 10% from the top
# # bottom_percent = 0.30  # Remove 15% from the bottom
# # # =================

# # # Open the image
# # image = Image.open(input_path)
# # width, height = image.size

# # # Convert percentages to pixels
# # top_crop = int(height * top_percent)
# # bottom_crop = int(height * bottom_percent)

# # # Calculate new crop box (left, top, right, bottom)
# # new_top = top_crop
# # new_bottom = height - bottom_crop

# # # Ensure valid crop
# # if new_bottom <= new_top:
# #     raise ValueError("Cropping values remove entire image. Adjust percentages.")

# # # Crop and save
# # cropped_image = image.crop((0, new_top, width, new_bottom))
# # cropped_image.save(output_path)

# # print(f"Cropped image saved as {output_path}")









# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from PIL import Image
# import time

# # === Crop Settings ===
# top_percent = 0.20     # Remove 20% from top
# bottom_percent = 0.30  # Remove 30% from bottom
# raw_path = "captcha_raw.png"       # First saved image
# output_path = "captcha_cropped.png"  # Final cropped image
# # =====================

# # Start Selenium
# driver = webdriver.Chrome()
# driver.get("https://appointment.theitalyvisa.com/Global/account/login")

# time.sleep(2)
# input("Press Enter after CAPTCHA is visible...")  # Wait for manual load

# # Locate captcha element and save directly to disk
# captcha_element = driver.find_element(By.XPATH, '//*[@id="captcha-main-div"]')
# captcha_element.screenshot(raw_path)

# driver.quit()

# # Open saved image with Pillow
# image = Image.open(raw_path)
# width, height = image.size

# # Convert percentages to pixels
# top_crop = int(height * top_percent)
# bottom_crop = int(height * bottom_percent)

# # Calculate crop box
# new_top = top_crop
# new_bottom = height - bottom_crop

# if new_bottom <= new_top:
#     raise ValueError("Cropping values remove entire image. Adjust percentages.")

# # Crop and save final image
# cropped_image = image.crop((0, new_top, width, new_bottom))
# cropped_image.save(output_path)

# print(f"Raw screenshot saved as {raw_path}")
# print(f"Cropped screenshot saved as {output_path}")








# import easyocr
# import re
# import cv2
# import numpy as np

# # Load image
# image_path = r"E:\Projects\skepta\Skepta\captcha_cropped.png"
# image = cv2.imread(image_path)

# # Initialize OCR
# reader = easyocr.Reader(['en'], gpu=False)

# # --- Step 1: Detect target number ---
# # Detect only from top strip of the image (full width, small height)
# header_h = int(image.shape[0] * 0.12)  # small strip at top
# header_img = image[:header_h, :]

# header_results = reader.readtext(header_img)
# target_number = None
# for (_, text, _) in header_results:
#     match = re.search(r'\b\d+\b', text)
#     if match:
#         target_number = match.group()
#         break

# print(f"🎯 Target number: {target_number}")

# # --- Step 2: Split into 3x3 grid like your original code ---
# rows, cols = 3, 3
# height, width = image.shape[:2]
# cell_h, cell_w = height // rows, width // cols

# for row in range(rows):
#     for col in range(cols):
#         idx = row * cols + col + 1
#         x1, y1 = col * cell_w, row * cell_h
#         x2, y2 = x1 + cell_w, y1 + cell_h
#         cell = image[y1:y2, x1:x2]

#         results = reader.readtext(cell)

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







# import cv2

# # === Step 1: Load the image ===
# image_path = "E:\Projects\skepta\Skepta\ML Model\captcha.png"  # Change to your image path
# img = cv2.imread(image_path)

# # === Step 2: Get dimensions ===
# height, width, _ = img.shape

# # === Step 3: Calculate split line ===
# split_line = int(height * 0.15)

# # === Step 4: Slice image ===
# header = img[:split_line, :]   # Top 20%
# body = img[split_line:, :]     # Bottom 80%

# # === Step 5: Save output ===
# cv2.imwrite("header.png", header)
# cv2.imwrite("body.png", body)

# print("✅ Saved 'header.png' and 'body.png'")










# import cv2
# import pytesseract
# import re

# # === Step 1: Read the header image ===
# image_path = "header.png"
# img = cv2.imread(image_path)

# # === Step 2: Convert to grayscale (optional but improves OCR) ===
# gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# # === Step 3: OCR with pytesseract ===
# # Use OCR Engine Mode 3 (default), Page Segmentation Mode 6 (Assume a single uniform block of text)
# custom_config = r'--oem 3 --psm 6'
# text = pytesseract.image_to_string(gray, config=custom_config)

# print("Detected text:", text)

# # === Step 4: Extract 3-digit number using regex ===
# match = re.search(r'\b(\d{3})\b', text)
# if match:
#     target_number = match.group(1)
#     print("✅ Target number:", target_number)
# else:
#     print("❌ No 3-digit number found.")










# import easyocr
# import re
# import cv2
# import numpy as np

# # Load image
# image_path = r"E:\Projects\skepta\Skepta\ML Model\body.png"
# image = cv2.imread(image_path)

# # Initialize OCR
# reader = easyocr.Reader(['en'], gpu=False)

# # --- Step 1: Detect target number ---
# # Detect only from top strip of the image (full width, small height)
# header_h = int(image.shape[0] * 0.12)  # small strip at top
# header_img = image[:header_h, :]

# header_results = reader.readtext(header_img)
# target_number = None
# for (_, text, _) in header_results:
#     match = re.search(r'\b\d+\b', text)
#     if match:
#         target_number = match.group()
#         break

# print(f"🎯 Target number: {target_number}")

# # --- Step 2: Split into 3x3 grid like your original code ---
# rows, cols = 3, 3
# height, width = image.shape[:2]
# cell_h, cell_w = height // rows, width // cols

# for row in range(rows):
#     for col in range(cols):
#         idx = row * cols + col + 1
#         x1, y1 = col * cell_w, row * cell_h
#         x2, y2 = x1 + cell_w, y1 + cell_h
#         cell = image[y1:y2, x1:x2]

#         results = reader.readtext(cell)

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














import time
import re
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from PIL import Image
import cv2
import easyocr


def capture_captcha_screenshot(url: str, captcha_xpath: str, raw_path: Path, wait_time: int = 2) -> None:
    """
    Opens a webpage using Selenium, waits for CAPTCHA to appear, captures its screenshot, and saves it.

    Args:
        url (str): URL to open.
        captcha_xpath (str): XPath of the captcha element.
        raw_path (Path): Path to save the raw captcha screenshot.
        wait_time (int): Seconds to wait after page load before asking user to confirm captcha visibility.
    """
    driver = webdriver.Chrome()
    driver.get(url)
    time.sleep(wait_time)
    input("Press Enter after CAPTCHA is visible...")

    try:
        captcha_element = driver.find_element(By.XPATH, captcha_xpath)
        captcha_element.screenshot(str(raw_path))
    finally:
        driver.quit()


def crop_image_vertically(
    input_path: Path, output_path: Path, top_percent: float, bottom_percent: float
) -> None:
    """
    Crops an image vertically by removing a percentage from top and bottom.

    Args:
        input_path (Path): Path of the image to crop.
        output_path (Path): Path to save the cropped image.
        top_percent (float): Percentage to remove from the top (0 < top_percent < 1).
        bottom_percent (float): Percentage to remove from the bottom (0 < bottom_percent < 1).
    """
    with Image.open(input_path) as img:
        width, height = img.size
        top_crop = int(height * top_percent)
        bottom_crop = int(height * bottom_percent)

        new_top = top_crop
        new_bottom = height - bottom_crop

        if new_bottom <= new_top:
            raise ValueError("Cropping percentages remove entire image. Adjust values.")

        cropped = img.crop((0, new_top, width, new_bottom))
        cropped.save(output_path)


def extract_target_number_easyocr(image_path: Path, top_strip_ratio: float = 0.12) -> str | None:
    """
    Extracts the first detected number from the top strip of an image using EasyOCR.

    Args:
        image_path (Path): Path to the image.
        top_strip_ratio (float): Portion of the image height to consider as the top strip.

    Returns:
        str | None: Extracted target number if found, else None.
    """
    image = cv2.imread(str(image_path))
    if image is None:
        raise FileNotFoundError(f"Image not found: {image_path}")

    height = image.shape[0]
    top_strip_height = int(height * top_strip_ratio)
    top_strip_img = image[:top_strip_height, :]

    reader = easyocr.Reader(['en'], gpu=False)
    results = reader.readtext(top_strip_img)

    for _, text, _ in results:
        match = re.search(r'\b\d+\b', text)
        if match:
            return match.group()
    return None


def split_image_grid(image_path: Path, rows: int, cols: int) -> list:
    """
    Splits an image into a grid of sub-images.

    Args:
        image_path (Path): Path to the image.
        rows (int): Number of rows.
        cols (int): Number of columns.

    Returns:
        list: List of sub-images as numpy arrays.
    """
    image = cv2.imread(str(image_path))
    if image is None:
        raise FileNotFoundError(f"Image not found: {image_path}")

    height, width = image.shape[:2]
    cell_h, cell_w = height // rows, width // cols

    cells = []
    for row in range(rows):
        for col in range(cols):
            y1 = row * cell_h
            y2 = y1 + cell_h
            x1 = col * cell_w
            x2 = x1 + cell_w
            cell = image[y1:y2, x1:x2]
            cells.append(cell)

    return cells


def ocr_numbers_from_cells(cells: list, reader: easyocr.Reader) -> list:
    """
    Performs OCR on a list of image cells and extracts numeric text with confidence.

    Args:
        cells (list): List of image cells (numpy arrays).
        reader (easyocr.Reader): Initialized EasyOCR reader object.

    Returns:
        list: List of tuples (cell_index, list of (number_text, confidence))
    """
    results_per_cell = []
    for idx, cell in enumerate(cells, start=1):
        ocr_results = reader.readtext(cell)
        numbers = [
            (text, prob)
            for (_, text, prob) in ocr_results
            if re.fullmatch(r'\d+(\.\d+)?', text)
        ]
        results_per_cell.append((idx, numbers))
    return results_per_cell


def main():
    # Settings
    url = "https://appointment.theitalyvisa.com/Global/account/login"
    captcha_xpath = '//*[@id="captcha-main-div"]'

    raw_captcha_path = Path("captcha_raw.png")
    cropped_captcha_path = Path("captcha_cropped.png")

    top_crop_percent = 0.20
    bottom_crop_percent = 0.30

    # Step 1: Capture captcha screenshot using Selenium
    print("Capturing CAPTCHA screenshot...")
    capture_captcha_screenshot(url, captcha_xpath, raw_captcha_path)

    # Step 2: Crop image vertically
    print("Cropping CAPTCHA image...")
    crop_image_vertically(raw_captcha_path, cropped_captcha_path, top_crop_percent, bottom_crop_percent)

    print(f"Raw captcha saved at {raw_captcha_path}")
    print(f"Cropped captcha saved at {cropped_captcha_path}")

    # Step 3: OCR on top strip for target number
    print("Extracting target number from top strip...")
    target_number = extract_target_number_easyocr(cropped_captcha_path)
    if target_number:
        print(f"🎯 Target number detected: {target_number}")
    else:
        print("⚠️ No target number detected.")

    # Step 4: Split image into 3x3 grid and perform OCR in each cell
    print("Splitting image into 3x3 grid and performing OCR on each cell...")
    cells = split_image_grid(cropped_captcha_path, rows=3, cols=3)
    reader = easyocr.Reader(['en'], gpu=False)
    cell_results = ocr_numbers_from_cells(cells, reader)

    for idx, numbers in cell_results:
        print(f"📦 Region {idx}:")
        if numbers:
            for num, confidence in numbers:
                print(f"  ➜ Number: {num} (Confidence: {confidence:.2f})")
        else:
            print("  ❌ No numeric text detected.")


if __name__ == "__main__":
    main()
