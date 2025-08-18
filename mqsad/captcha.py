import time
import re
import random
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from PIL import Image
import cv2
import easyocr

from selenium_stealth import stealth

# ====== USER SETTINGS ======
user_email = "justarandomemail785@gmail.com"  # Expected email text inside <b>
case1_coords = [
    (626, 276), (732, 277), (850, 282),
    (621, 389), (735, 390), (850, 295),
    (626, 501), (734, 500), (845, 500)
]
case2_coords = []  # TODO: Fill when provided
# ===========================

def get_viewport_relative_coords(driver, screen_x, screen_y):
    """Convert screen coordinates to viewport-relative coordinates."""
    # Get browser window position and size
    window_rect = driver.execute_script("""
        return {
            x: window.screenX,
            y: window.screenY,
            width: window.innerWidth,
            height: window.innerHeight
        };
    """)
    
    print(f"🔍 Browser window position: ({window_rect['x']}, {window_rect['y']})")
    print(f"📏 Browser window size: {window_rect['width']}x{window_rect['height']}")
    print(f"📍 Target screen coordinates: ({screen_x}, {screen_y})")
    
    # Calculate viewport-relative coordinates
    viewport_x = screen_x - window_rect['x']
    viewport_y = screen_y - window_rect['y']
    
    print(f"🎯 Viewport-relative coordinates: ({viewport_x}, {viewport_y})")
    
    # Check if coordinates are within viewport
    if viewport_x < 0 or viewport_y < 0:
        print(f"⚠️ WARNING: Coordinates are outside viewport (negative position)")
    if viewport_x > window_rect['width'] or viewport_y > window_rect['height']:
        print(f"⚠️ WARNING: Coordinates are outside viewport (beyond window dimensions)")
    
    return viewport_x, viewport_y


def human_like_click(driver, screen_x, screen_y):
    """
    Simulate human-like mouse movement and clicking behavior with proper coordinate handling.
    
    Args:
        driver: WebDriver instance
        screen_x: X coordinate on the screen
        screen_y: Y coordinate on the screen
    """
    try:
        # Convert screen coordinates to viewport-relative coordinates
        x, y = get_viewport_relative_coords(driver, screen_x, screen_y)
        
        print(f"🖱️ Preparing human-like click at viewport coordinates ({x}, {y})")
        
        # Verify coordinates are within reasonable bounds
        if x < 0 or y < 0 or x > 3000 or y > 3000:
            print(f"❌ Invalid coordinates detected: ({x}, {y})")
            return False
            
        actions = ActionChains(driver)
        
        # Start from a random position on screen (simulates moving mouse from elsewhere)
        start_x = random.randint(50, 200)
        start_y = random.randint(50, 200)
        print(f"⮞ Starting movement from ({start_x}, {start_y})")
        actions.move_by_offset(start_x, start_y)
        actions.pause(random.uniform(0.2, 0.5))
        
        # Approach the target in multiple steps with randomness
        num_steps = random.randint(3, 6)
        print(f"⮞ Creating {num_steps} movement steps to target")
        
        for i in range(num_steps):
            # Calculate progress along the path (using easing function for natural movement)
            t = (i + 1) / num_steps
            progress = t * t * (3 - 2 * t)  # Ease-in-out function
            
            # Calculate target position with some randomness
            target_x = int(x * progress)
            target_y = int(y * progress)
            
            # Add random deviation (less as we get closer to target)
            max_deviation = 15 * (1 - progress)
            deviation_x = random.uniform(-max_deviation, max_deviation)
            deviation_y = random.uniform(-max_deviation, max_deviation)
            
            # Calculate relative movement from previous position
            if i == 0:
                rel_x = target_x + deviation_x
                rel_y = target_y + deviation_y
            else:
                prev_progress = (i / num_steps)
                prev_x = int(x * prev_progress * (3 - 2 * prev_progress))
                prev_y = int(y * prev_progress * (3 - 2 * prev_progress))
                rel_x = (target_x + deviation_x) - prev_x
                rel_y = (target_y + deviation_y) - prev_y
            
            print(f"  Step {i+1}: Moving by ({int(rel_x)}, {int(rel_y)}) with pause {random.uniform(0.05, 0.25):.2f}s")
            
            # Move to this position
            actions.move_by_offset(int(rel_x), int(rel_y))
            
            # Vary the speed of movement
            actions.pause(random.uniform(0.05, 0.25))
        
        # Add a tiny jiggle before clicking (30% chance)
        if random.random() < 0.3:
            jiggle_x = random.randint(-3, 3)
            jiggle_y = random.randint(-3, 3)
            print(f"  ✨ Adding human-like jiggle: ({jiggle_x}, {jiggle_y})")
            actions.move_by_offset(jiggle_x, jiggle_y)
            actions.pause(random.uniform(0.05, 0.15))
            actions.move_by_offset(-jiggle_x, -jiggle_y)
            actions.pause(random.uniform(0.05, 0.15))
        
        # Add small random offset to final click position
        final_offset_x = random.randint(-5, 5)
        final_offset_y = random.randint(-5, 5)
        print(f"  🎯 Final offset: ({final_offset_x}, {final_offset_y})")
        actions.move_by_offset(final_offset_x, final_offset_y)
        
        # Natural click timing with slight variation
        click_delay = random.uniform(0.05, 0.2)
        print(f"  ✅ Clicking after {click_delay:.2f}s delay")
        actions.pause(click_delay)
        actions.click()
        
        # Execute the action sequence
        print("  ⏩ Executing action sequence...")
        actions.perform()
        print("  ✔️ Click completed successfully")
        
        # Return to original position
        actions.move_by_offset(-x, -y)
        actions.perform()
        
        # Random delay after click
        delay = random.uniform(0.3, 0.8)
        print(f"  ⏳ Waiting {delay:.2f}s before next action")
        time.sleep(delay)
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR during human_like_click: {str(e)}")
        # Try a fallback method - move to center and click
        try:
            print("  ⚠️ Attempting fallback click method...")
            actions = ActionChains(driver)
            actions.move_to_element_with_offset(driver.find_element(By.TAG_NAME, "body"), x, y)
            actions.click()
            actions.perform()
            print("  ✔️ Fallback click successful")
            return True
        except Exception as fallback_error:
            print(f"  ❌ Fallback click also failed: {str(fallback_error)}")
            return False

def click_matching_images(driver, coords, matches):
    """Click on images with coordinates where matches[i] is True, using human-like behavior."""
    for idx, match in enumerate(matches):
        if match:
            x, y = coords[idx]
            print(f"\n{'='*50}")
            print(f"🖱️ Attempting to click on coordinates ({x}, {y}) - Index {idx+1}")
            print(f"{'='*50}")
            
            success = human_like_click(driver, x, y)
            if not success:
                print(f"❌ Failed to click on coordinates ({x}, {y})")
                # Optional: add additional recovery steps here

def capture_captcha_screenshot(driver, captcha_xpath: str, raw_path: Path):
    """Wait for Enter, check <b> text, return case number."""
    input("Press Enter after CAPTCHA is visible...")

    # Read <b> text
    b_element = driver.find_element(By.XPATH, '//*[@id="captcha-main-div"]/div[1]/div[1]/b')
    b_text = b_element.text.strip()

    # Case check
    if b_text.lower() == user_email.lower():
        print("✅ Case 1 detected.")
        case_number = 1
    else:
        print("✅ Case 2 detected.")
        case_number = 2

    # Capture captcha screenshot
    captcha_element = driver.find_element(By.XPATH, captcha_xpath)
    captcha_element.screenshot(str(raw_path))

    return case_number


def crop_image_vertically(input_path: Path, output_path: Path, top_percent: float, bottom_percent: float):
    """Crop image vertically by removing a percentage from top and bottom."""
    with Image.open(input_path) as img:
        width, height = img.size
        top_crop = int(height * top_percent)
        bottom_crop = int(height * bottom_percent)

        new_top = top_crop
        new_bottom = height - bottom_crop
        if new_bottom <= new_top:
            raise ValueError("Cropping percentages remove entire image.")

        cropped = img.crop((0, new_top, width, new_bottom))
        cropped.save(output_path)


def extract_target_number_easyocr(image_path: Path, top_strip_ratio: float = 0.12) -> str | None:
    """Extract first number from top strip of image."""
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
            num = match.group()
            if len(num) == 4:
                num = num[1:]  # Remove first digit if 4-digit
            return num
    return None


def split_image_grid(image_path: Path, rows: int, cols: int) -> list:
    """Split image into grid cells."""
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
    """OCR on each cell, return number or None."""
    output = []
    for cell in cells:
        ocr_results = reader.readtext(cell)
        if ocr_results:
            for (_, text, _) in ocr_results:
                if re.fullmatch(r'\d+(\.\d+)?', text):
                    if len(text) == 4:  # Remove first digit if 4-digit
                        text = text[1:]
                    output.append(text)
                    break
            else:
                output.append(None)
        else:
            output.append(None)
    return output




def main():
    url = "https://appointment.theitalyvisa.com/Global/account/login"
    captcha_xpath = '//*[@id="captcha-main-div"]'

    raw_captcha_path = Path("captcha_raw.png")
    cropped_captcha_path = Path("captcha_cropped.png")

    top_crop_percent = 0.20
    bottom_crop_percent = 0.30

    # ==== MOBILE EMULATION + STEALTH (replaces webdriver.Chrome() + set_window_size) ====
    mobile_emulation = {
        "deviceMetrics": {"width": 375, "height": 812, "pixelRatio": 3.0},
        "userAgent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_6 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 "
            "Mobile/15E148 Safari/604.1"
        ),
    }
    options = webdriver.ChromeOptions()
    options.add_experimental_option("mobileEmulation", mobile_emulation)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=options)

    # remove navigator.webdriver and apply stealth tweaks
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
    )
    stealth(
        driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="iPhone",
        webgl_vendor="Apple Inc.",
        renderer="Apple GPU",
        fix_hairline=True,
    )
    # ================================================================================

    driver.get(url)

    time.sleep(2)

    # Step 1: Wait, check case, capture screenshot
    case_number = capture_captcha_screenshot(driver, captcha_xpath, raw_captcha_path)

    # Step 2: Crop
    crop_image_vertically(raw_captcha_path, cropped_captcha_path, top_crop_percent, bottom_crop_percent)

    # Step 3: OCR target number
    target_number = extract_target_number_easyocr(cropped_captcha_path)
    print(f"🎯 Target number: {target_number}")

    # Step 4: OCR 9 images
    cells = split_image_grid(cropped_captcha_path, rows=3, cols=3)
    reader = easyocr.Reader(['en'], gpu=False)
    image_numbers = ocr_numbers_from_cells(cells, reader)

    # Step 5: Build final array
    output_array = [target_number] + image_numbers
    print("✅ Final array:", output_array)

    # Step 6: Compare & click
    matches = [(num == target_number) if num is not None else False for num in image_numbers]
    if case_number == 1:
        click_matching_images(driver, case1_coords, matches)
    elif case_number == 2:
        if not case2_coords:
            print("⚠️ Case 2 coords not provided, skipping clicks.")
        else:
            click_matching_images(driver, case2_coords, matches)

    input("\nPress Enter to exit...")
    driver.quit()


if __name__ == "__main__":
    main()

