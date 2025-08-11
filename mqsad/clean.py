# from PIL import Image

# # === Settings ===
# input_path = "captcha.png"          # Original image
# output_path = "captcha_cropped.png" # Cropped image

# top_percent = 0.20     # Remove 10% from the top
# bottom_percent = 0.30  # Remove 15% from the bottom
# # =================

# # Open the image
# image = Image.open(input_path)
# width, height = image.size

# # Convert percentages to pixels
# top_crop = int(height * top_percent)
# bottom_crop = int(height * bottom_percent)

# # Calculate new crop box (left, top, right, bottom)
# new_top = top_crop
# new_bottom = height - bottom_crop

# # Ensure valid crop
# if new_bottom <= new_top:
#     raise ValueError("Cropping values remove entire image. Adjust percentages.")

# # Crop and save
# cropped_image = image.crop((0, new_top, width, new_bottom))
# cropped_image.save(output_path)

# print(f"Cropped image saved as {output_path}")









from selenium import webdriver
from selenium.webdriver.common.by import By
from PIL import Image
import time

# === Crop Settings ===
top_percent = 0.20     # Remove 20% from top
bottom_percent = 0.30  # Remove 30% from bottom
raw_path = "captcha_raw.png"       # First saved image
output_path = "captcha_cropped.png"  # Final cropped image
# =====================

# Start Selenium
driver = webdriver.Chrome()
driver.get("https://appointment.theitalyvisa.com/Global/account/login")

time.sleep(2)
input("Press Enter after CAPTCHA is visible...")  # Wait for manual load

# Locate captcha element and save directly to disk
captcha_element = driver.find_element(By.XPATH, '//*[@id="captcha-main-div"]')
captcha_element.screenshot(raw_path)

driver.quit()

# Open saved image with Pillow
image = Image.open(raw_path)
width, height = image.size

# Convert percentages to pixels
top_crop = int(height * top_percent)
bottom_crop = int(height * bottom_percent)

# Calculate crop box
new_top = top_crop
new_bottom = height - bottom_crop

if new_bottom <= new_top:
    raise ValueError("Cropping values remove entire image. Adjust percentages.")

# Crop and save final image
cropped_image = image.crop((0, new_top, width, new_bottom))
cropped_image.save(output_path)

print(f"Raw screenshot saved as {raw_path}")
print(f"Cropped screenshot saved as {output_path}")








import easyocr
import re
import cv2
import numpy as np

# Load image
image_path = r"E:\Projects\skepta\Skepta\captcha_cropped.png"
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







import cv2

# === Step 1: Load the image ===
image_path = "E:\Projects\skepta\Skepta\ML Model\captcha.png"  # Change to your image path
img = cv2.imread(image_path)

# === Step 2: Get dimensions ===
height, width, _ = img.shape

# === Step 3: Calculate split line ===
split_line = int(height * 0.15)

# === Step 4: Slice image ===
header = img[:split_line, :]   # Top 20%
body = img[split_line:, :]     # Bottom 80%

# === Step 5: Save output ===
cv2.imwrite("header.png", header)
cv2.imwrite("body.png", body)

print("✅ Saved 'header.png' and 'body.png'")










import cv2
import pytesseract
import re

# === Step 1: Read the header image ===
image_path = "header.png"
img = cv2.imread(image_path)

# === Step 2: Convert to grayscale (optional but improves OCR) ===
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# === Step 3: OCR with pytesseract ===
# Use OCR Engine Mode 3 (default), Page Segmentation Mode 6 (Assume a single uniform block of text)
custom_config = r'--oem 3 --psm 6'
text = pytesseract.image_to_string(gray, config=custom_config)

print("Detected text:", text)

# === Step 4: Extract 3-digit number using regex ===
match = re.search(r'\b(\d{3})\b', text)
if match:
    target_number = match.group(1)
    print("✅ Target number:", target_number)
else:
    print("❌ No 3-digit number found.")











