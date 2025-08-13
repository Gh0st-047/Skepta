import time
import re
import cv2
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from PIL import Image
import easyocr

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC




def setup_driver():
    """Set up a Chrome driver with basic stealth settings"""
    options = webdriver.ChromeOptions()
    options.add_argument("--incognito")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    
    # Hide webdriver property
    driver.execute_script("""
        Object.defineProperty(navigator, 'webdriver', {
          get: () => undefined
        })
    """)
    
    return driver


def capture_captcha_screenshot(driver, captcha_xpath: str, raw_path: str, wait_time: int = 2) -> None:
    """
    Captures CAPTCHA screenshot without closing the driver.
    
    Args:
        driver: WebDriver instance
        captcha_xpath (str): XPath of the captcha element.
        raw_path (str): Path to save the raw captcha screenshot.
        wait_time (int): Seconds to wait after page load.
    """
    time.sleep(wait_time)
    
    try:
        captcha_element = driver.find_element(By.XPATH, captcha_xpath)
        captcha_element.screenshot(raw_path)
        return captcha_element
    except Exception as e:
        print(f"Error capturing CAPTCHA screenshot: {str(e)}")
        return None


def crop_image_vertically(
    input_path: str, output_path: str, top_percent: float, bottom_percent: float
) -> None:
    """
    Crops an image vertically by removing a percentage from top and bottom.
    
    Args:
        input_path (str): Path of the image to crop.
        output_path (str): Path to save the cropped image.
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


def extract_target_number_easyocr(image_path: str, top_strip_ratio: float = 0.12) -> str | None:
    """
    Extracts the first detected number from the top strip of an image using EasyOCR.
    
    Args:
        image_path (str): Path to the image.
        top_strip_ratio (float): Portion of the image height to consider as the top strip.
    
    Returns:
        str | None: Extracted target number if found, else None.
    """
    image = cv2.imread(image_path)
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


def split_image_grid(image_path: str, rows: int, cols: int) -> list:
    """
    Splits an image into a grid of sub-images.
    
    Args:
        image_path (str): Path to the image.
        rows (int): Number of rows.
        cols (int): Number of columns.
    
    Returns:
        list: List of sub-images as numpy arrays.
    """
    image = cv2.imread(image_path)
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


def ocr_numbers_from_cells(cells: list, reader: easyocr.Reader, target_number: str) -> list:
    """
    Performs OCR on a list of image cells and identifies cells with the target number.
    
    Args:
        cells (list): List of image cells (numpy arrays).
        reader (easyocr.Reader): Initialized EasyOCR reader object.
        target_number (str): The target number to look for.
    
    Returns:
        list: List of cell indices that contain the target number.
    """
    target_cells = []
    
    for idx, cell in enumerate(cells):
        ocr_results = reader.readtext(cell)
        for (_, text, prob) in ocr_results:
            # Remove non-digit characters
            cleaned_text = re.sub(r'\D', '', text)
            if cleaned_text == target_number and prob > 0.4:
                target_cells.append(idx)
                break
    
    return target_cells


def get_captcha_tiles(driver):
    """
    Gets the actual CAPTCHA tile elements from the webpage.
    
    Returns:
        list: List of tile elements in the correct order.
    """
    try:
        # Find the CAPTCHA container
        captcha_container = driver.find_element(By.ID, "captcha-main-div")
        
        # Find all potential tile elements - this is the critical fix
        # Look for divs with "padding:5px;" in their style and containing img.captcha-img
        potential_tiles = driver.find_elements(By.CSS_SELECTOR, "div[style*='padding:5px;']")
        
        # Filter for elements that:
        # 1. Contain the captcha-img
        # 2. Are actually visible
        tile_elements = []
        for tile in potential_tiles:
            try:
                # Check if it has the captcha-img
                has_captcha_img = driver.execute_script(
                    "return arguments[0].querySelector('img.captcha-img') !== null;",
                    tile
                )
                
                # Check if it's actually visible
                is_visible = driver.execute_script("""
                    var el = arguments[0];
                    var style = window.getComputedStyle(el);
                    return style.display !== 'none' && 
                           style.visibility !== 'hidden' && 
                           el.offsetWidth > 0 && 
                           el.offsetHeight > 0;
                """, tile)
                
                if has_captcha_img and is_visible:
                    tile_elements.append(tile)
            except Exception as e:
                print(f"Error checking tile properties: {str(e)}")
        
        print(f"Found {len(tile_elements)} potential CAPTCHA tiles")
        
        # We should have exactly 9 tiles for a 3x3 grid
        if len(tile_elements) >= 9:
            # Sort the tiles by their position on the page (top to bottom, left to right)
            tile_elements.sort(key=lambda tile: (tile.location['y'], tile.location['x']))
            return tile_elements[:9]  # Return the first 9 tiles
        else:
            print(f"Warning: Expected at least 9 tiles but found {len(tile_elements)}")
            return tile_elements
            
    except Exception as e:
        print(f"Error getting CAPTCHA tiles: {str(e)}")
        return []


def click_captcha_tiles(driver, tile_elements, cell_indices):
    """
    Clicks the CAPTCHA tiles corresponding to the given cell indices.
    
    Args:
        driver: WebDriver instance
        tile_elements: List of tile elements
        cell_indices: List of cell indices to click (0-8)
    """
    # Sort tiles by position to ensure they're in the correct order
    tile_elements.sort(key=lambda tile: (tile.location['y'], tile.location['x']))
    
    for idx in cell_indices:
        if 0 <= idx < len(tile_elements):
            print(f"Clicking tile at position {idx+1}...")
            ActionChains(driver).move_to_element(tile_elements[idx]).click().perform()
            time.sleep(0.5)  # Small delay between clicks
        else:
            print(f"Warning: Cell index {idx} is out of range")


def main():
    # Settings
    url = "https://appointment.theitalyvisa.com/Global/account/login"
    captcha_xpath = '//*[@id="captcha-main-div"]'

    raw_captcha_path = "captcha_raw.png"
    cropped_captcha_path = "captcha_cropped.png"

    top_crop_percent = 0.20
    bottom_crop_percent = 0.30

    # Step 1: Set up driver and open URL
    print("Setting up browser...")
    driver = setup_driver()
    driver.get(url)
    input("Press Enter to start the CAPTCHA solving process...")

    
    # Wait for CAPTCHA to load
    try:
        print("Waiting for CAPTCHA to load...")

        captcha_element = WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.ID, "captcha-main-div"))
        )
        print("CAPTCHA is visible")
    except Exception as e:
        print(f"Error: CAPTCHA did not load properly: {str(e)}")
        driver.quit()
        return

    # Step 2: Capture CAPTCHA screenshot
    print("Capturing CAPTCHA screenshot...")
    captcha_element = capture_captcha_screenshot(driver, captcha_xpath, raw_captcha_path)
    if not captcha_element:
        print("Failed to capture CAPTCHA screenshot")
        driver.quit()
        return

    # Step 3: Crop image vertically
    print("Cropping CAPTCHA image...")
    crop_image_vertically(raw_captcha_path, cropped_captcha_path, top_crop_percent, bottom_crop_percent)

    print(f"Raw captcha saved at {raw_captcha_path}")
    print(f"Cropped captcha saved at {cropped_captcha_path}")

    # Step 4: OCR on top strip for target number
    print("Extracting target number from top strip...")
    target_number = extract_target_number_easyocr(cropped_captcha_path)
    if target_number:
        print(f"🎯 Target number detected: {target_number}")
    else:
        print("⚠️ No target number detected.")
        driver.quit()
        return

    # Step 5: Split image into 3x3 grid and perform OCR in each cell
    print("Splitting image into 3x3 grid and performing OCR on each cell...")
    cells = split_image_grid(cropped_captcha_path, rows=3, cols=3)
    reader = easyocr.Reader(['en'], gpu=False)
    target_cells = ocr_numbers_from_cells(cells, reader, target_number)

    # Print results
    for idx, cell in enumerate(cells):
        print(f"📦 Region {idx+1}:")
        cell_results = reader.readtext(cell)
        numbers = [
            (text, prob)
            for (_, text, prob) in cell_results
            if re.fullmatch(r'\d+(\.\d+)?', text)
        ]
        if numbers:
            for num, confidence in numbers:
                status = "✅" if num == target_number else "➜"
                print(f"  {status} Number: {num} (Confidence: {confidence:.2f})")
        else:
            print("  ❌ No numeric text detected.")

    # Step 6: Get the actual CAPTCHA tile elements from the webpage
    print("Getting CAPTCHA tile elements from webpage...")
    tile_elements = get_captcha_tiles(driver)
    
    if not tile_elements or len(tile_elements) < 9:
        print("Error: Could not find enough CAPTCHA tiles on the webpage")
        # Try to find tiles using alternative method
        print("Trying alternative method to find CAPTCHA tiles...")
        try:
            # This is the alternative method - find all div.col-4 elements
            tile_elements = driver.find_elements(By.CSS_SELECTOR, "div.col-4")
            
            # Filter for visible elements with captcha-img
            filtered_tiles = []
            for tile in tile_elements:
                try:
                    has_captcha_img = driver.execute_script(
                        "return arguments[0].querySelector('img.captcha-img') !== null;",
                        tile
                    )
                    is_visible = driver.execute_script("""
                        var el = arguments[0];
                        var style = window.getComputedStyle(el);
                        return style.display !== 'none' && 
                               style.visibility !== 'hidden' && 
                               el.offsetWidth > 0 && 
                               el.offsetHeight > 0;
                    """, tile)
                    if has_captcha_img and is_visible:
                        filtered_tiles.append(tile)
                except:
                    pass
            
            # Sort and take first 9
            filtered_tiles.sort(key=lambda tile: (tile.location['y'], tile.location['x']))
            tile_elements = filtered_tiles[:9]
            
            if len(tile_elements) >= 9:
                print(f"Found {len(tile_elements)} CAPTCHA tiles using alternative method")
            else:
                print(f"Still only found {len(tile_elements)} CAPTCHA tiles")
        except Exception as e:
            print(f"Alternative method failed: {str(e)}")
    
    if not tile_elements or len(tile_elements) < 9:
        print("Error: Could not find enough CAPTCHA tiles on the webpage")
        driver.quit()
        return

    # Step 7: Click the tiles that contain the target number
    print(f"Clicking {len(target_cells)} tiles with the target number...")
    click_captcha_tiles(driver, tile_elements, target_cells)

    # Wait for user to see the result
    input("CAPTCHA solving complete. Press Enter to close the browser...")
    driver.quit()


if __name__ == "__main__":
    main()