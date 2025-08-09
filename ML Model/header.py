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
