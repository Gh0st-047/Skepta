from selenium import webdriver
from selenium.webdriver.common.by import By
from PIL import Image
import time
import io

driver = webdriver.Chrome()
driver.get("https://appointment.theitalyvisa.com/Global/account/login")

time.sleep(2) 
input("Press Enter after CAPTCHA is visible...")  # Wait for manual load

# Locate the captcha element
captcha_element = driver.find_element(By.XPATH, '//*[@id="captcha-main-div"]')

# Screenshot into memory
png_bytes = captcha_element.screenshot_as_png
image = Image.open(io.BytesIO(png_bytes))

width, height = image.size

# Crop percentages
top_percent = 0     # remove 10% from top
bottom_percent = 0  # remove 15% from bottom

# Convert to pixels
top_crop = int(height * top_percent)
bottom_crop = int(height * bottom_percent)

# Ensure valid cropping
new_top = top_crop
new_bottom = height - bottom_crop
if new_bottom <= new_top:
    raise ValueError("Cropping values remove entire image. Adjust percentages.")

cropped_image = image.crop((0, new_top, width, new_bottom))
cropped_image.save("captcha_cropped.png")

print("Cropped screenshot saved as captcha_cropped.png")
driver.quit()



