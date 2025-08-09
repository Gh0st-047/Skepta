import cv2

# === Step 1: Load the image ===
image_path = "captcha.png"  # Change to your image path
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
