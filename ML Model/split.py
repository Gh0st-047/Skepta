import cv2
import easyocr
import pytesseract
import numpy as np
import re
import os


def split_image(image_path, split_ratio=0.15):
    img = cv2.imread(image_path)
    height, width = img.shape[:2]
    split_line = int(height * split_ratio)
    header = img[:split_line, :]
    body = img[split_line:, :]
    return header, body

def extract_target_number(header_img):
    gray = cv2.cvtColor(header_img, cv2.COLOR_BGR2GRAY)
    custom_config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(gray, config=custom_config)
    print("🔎 Header text:", text.strip())

    match = re.search(r'\b(\d{3})\b', text)
    if match:
        return match.group(1)
    return None

def extract_grid_numbers(body_img, rows=3, cols=3):
    reader = easyocr.Reader(['en'], gpu=False)
    height, width = body_img.shape[:2]
    cell_h, cell_w = height // rows, width // cols
    numbers = []

    for row in range(rows):
        for col in range(cols):
            idx = row * cols + col + 1
            x1, y1 = col * cell_w, row * cell_h
            x2, y2 = x1 + cell_w, y1 + cell_h
            cell = body_img[y1:y2, x1:x2]

            results = reader.readtext(cell)
            numeric_results = [
                (text, prob) for (bbox, text, prob) in results
                if re.fullmatch(r'\d+(\.\d+)?', text)
            ]

            if numeric_results:
                # Pick the highest confidence match
                best = max(numeric_results, key=lambda x: x[1])
                numbers.append((idx, best[0], best[1]))
            else:
                numbers.append((idx, None, 0.0))  # Indicate failure

    return numbers

def main():
    image_path = "E:\Projects\skepta\Skepta\ML Model\captcha.png"  # Or pass via argparse for flexibility
    header_img, body_img = split_image(image_path)

    print("🔷 Step 1: Extracting target number from header...")
    target_number = extract_target_number(header_img)
    if target_number:
        print(f"✅ Target number detected: {target_number}\n")
    else:
        print("❌ Could not detect target number.\n")

    print("🔷 Step 2: Extracting 3x3 grid numbers...")
    grid_numbers = extract_grid_numbers(body_img)

    for idx, num, conf in grid_numbers:
        if num:
            print(f"📦 Cell {idx}: {num} (Confidence: {conf:.2f})")
        else:
            print(f"📦 Cell {idx}: ❌ No number detected")

if __name__ == "__main__":
    main()
