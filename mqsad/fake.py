import time
import re
import cv2
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from PIL import Image
import easyocr
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


def preprocess_cell_image(cell_image):
    """
    Preprocess a cell image to improve OCR accuracy.
    
    Args:
        cell_image: Image of a single cell
        
    Returns:
        Preprocessed image
    """
    # Convert to grayscale
    gray = cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY)
    
    # Apply thresholding to get a binary image
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Apply morphological operations to clean up the image
    kernel = np.ones((2,2), np.uint8)
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    return cleaned


def calculate_number_similarity(num1, num2):
    """
    Calculate similarity between two numbers (0-100%).
    
    Args:
        num1: First number as string
        num2: Second number as string
        
    Returns:
        Similarity percentage
    """
    if len(num1) != len(num2):
        return 0
    
    match_count = sum(1 for a, b in zip(num1, num2) if a == b)
    return (match_count / len(num1)) * 100


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
    target_len = len(target_number)
    
    print(f"\n🔍 Analyzing cells for target number: {target_number}")
    
    for idx, cell in enumerate(cells):
        # Preprocess the cell image to improve OCR
        preprocessed_cell = preprocess_cell_image(cell)
        
        ocr_results = reader.readtext(preprocessed_cell)
        
        found_match = False
        for (_, text, prob) in ocr_results:
            # Remove non-digit characters
            cleaned_text = re.sub(r'\D', '', text)
            
            if not cleaned_text:
                continue
                
            # Calculate similarity to target number
            similarity = calculate_number_similarity(cleaned_text, target_number)
            
            # Case 1: Exact match with reasonable confidence
            if cleaned_text == target_number:
                if prob > 0.4:
                    print(f"  ✅ EXACT MATCH: Cell {idx+1} contains {cleaned_text} (Confidence: {prob:.2f})")
                    target_cells.append(idx)
                    found_match = True
                    break
            
            # Case 2: Close match with high confidence (allow 1 digit difference)
            elif len(cleaned_text) == target_len and prob > 0.7 and similarity >= 66.7:
                print(f"  ⚠️ CLOSE MATCH: Cell {idx+1} has {cleaned_text} (Confidence: {prob:.2f}, {similarity:.1f}% similar to {target_number})")
                target_cells.append(idx)
                found_match = True
                break
            
            # Case 3: Exact length match with medium confidence
            elif len(cleaned_text) == target_len and prob > 0.5:
                print(f"  ➜ Possible match: Cell {idx+1} has {cleaned_text} (Confidence: {prob:.2f}, {similarity:.1f}% similar to {target_number})")
        
        if not found_match and ocr_results:
            print(f"  ❌ Cell {idx+1} has no matching number")
        elif not ocr_results:
            print(f"  ❌ Cell {idx+1} has no detected text")
    
    return target_cells


def get_captcha_tiles(driver):
    """
    Gets the actual CAPTCHA tile elements from the webpage.
    
    Returns:
        list: List of tile elements in the correct order.
    """
    print("[CAPTCHA] Finding CAPTCHA tiles with bulletproof method...")
    
    try:
        # 1. Find the CAPTCHA container
        captcha_container = driver.find_element(By.ID, "captcha-main-div")
        print("[CAPTCHA] Found CAPTCHA container with ID 'captcha-main-div'")
        
        # 2. Find the main div container
        try:
            main_div = captcha_container.find_element(By.CSS_SELECTOR, ".main-div-container")
            print("[CAPTCHA] Found main div container")
        except:
            # Alternative approach if the class name is randomized
            main_div = driver.execute_script("""
                var container = document.getElementById('captcha-main-div');
                if (container) {
                    for (var i = 0; i < container.children.length; i++) {
                        var child = container.children[i];
                        if (child.classList && child.classList.contains('col-12')) {
                            return child;
                        }
                    }
                }
                return null;
            """)
            print("[CAPTCHA] Found main div container using JavaScript")
        
        if not main_div:
            print("[CAPTCHA] Could not find main div container")
            return []
        
        # 3. Find the row container that holds the CAPTCHA tiles
        try:
            # Use a more flexible selector for the row
            tiles_row = main_div.find_element(By.CSS_SELECTOR, "div.row")
            print("[CAPTCHA] Found tiles row container using CSS selector")
        except:
            try:
                # Use JavaScript to find the row with position:relative
                tiles_row = driver.execute_script("""
                    var mainDiv = arguments[0];
                    if (mainDiv) {
                        var rows = mainDiv.querySelectorAll('div.row');
                        for (var i = 0; i < rows.length; i++) {
                            var style = window.getComputedStyle(rows[i]);
                            if (style.position === 'relative') {
                                return rows[i];
                            }
                        }
                    }
                    return null;
                """, main_div)
                print("[CAPTCHA] Found tiles row container using JavaScript")
            except Exception as e:
                print(f"[CAPTCHA] Error finding tiles row container: {str(e)}")
                return []
        
        if not tiles_row:
            print("[CAPTCHA] Could not find tiles row container")
            return []
        
        # 4. Find all direct children of the row container
        all_elements = tiles_row.find_elements(By.XPATH, "./*")
        print(f"[CAPTCHA] Found {len(all_elements)} elements in the CAPTCHA row container")
        
        # 5. Take every second element starting from index 1 (the tile elements)
        tile_elements = []
        for i in range(1, len(all_elements), 2):
            if i < len(all_elements):
                tile = all_elements[i]
                tile_elements.append(tile)
        
        print(f"[CAPTCHA] Found {len(tile_elements)} tile elements by position")
        
        # 6. Filter for elements that contain the captcha-img
        filtered_tiles = []
        for tile in tile_elements:
            try:
                # Check if it has the captcha-img
                has_captcha_img = driver.execute_script(
                    "return arguments[0].querySelector('img.captcha-img') !== null;",
                    tile
                )
                
                if has_captcha_img:
                    filtered_tiles.append(tile)
            except Exception as e:
                print(f"[CAPTCHA] Error checking for captcha-img: {str(e)}")
        
        print(f"[CAPTCHA] Found {len(filtered_tiles)} tiles with captcha-img")
        
        # 7. If we have more than 9 tiles, take the first 9
        if len(filtered_tiles) > 9:
            print(f"[CAPTCHA] Taking first 9 tiles (found {len(filtered_tiles)})")
            filtered_tiles = filtered_tiles[:9]
        
        # 8. If we have fewer than 9 tiles, try an alternative approach
        if len(filtered_tiles) < 9:
            print(f"[CAPTCHA] Warning: Only found {len(filtered_tiles)} tiles, trying alternative approach...")
            
            # Alternative approach: Find all divs with style containing "padding:5px;" and img.captcha-img
            alt_tiles = driver.find_elements(By.CSS_SELECTOR, "div[style*='padding:5px;']")
            print(f"[CAPTCHA] Found {len(alt_tiles)} elements with padding:5px;")
            
            alt_filtered = []
            for tile in alt_tiles:
                try:
                    has_captcha_img = driver.execute_script(
                        "return arguments[0].querySelector('img.captcha-img') !== null;",
                        tile
                    )
                    if has_captcha_img:
                        alt_filtered.append(tile)
                except:
                    pass
            
            # Sort by position to get the correct order
            alt_filtered.sort(key=lambda t: (t.location['y'], t.location['x']))
            
            print(f"[CAPTCHA] Found {len(alt_filtered)} alternative tiles with captcha-img")
            
            if len(alt_filtered) >= 9:
                filtered_tiles = alt_filtered[:9]
                print(f"[CAPTCHA] Using alternative tiles (found {len(filtered_tiles)})")
        
        # 9. Final check - we need exactly 9 tiles
        if len(filtered_tiles) != 9:
            print(f"[CAPTCHA] ERROR: Expected 9 tiles but found {len(filtered_tiles)}")
            return []
        
        print(f"[CAPTCHA] Successfully identified {len(filtered_tiles)} CAPTCHA tiles")
        return filtered_tiles
            
    except Exception as e:
        print(f"[CAPTCHA] Error getting CAPTCHA tiles: {str(e)}")
        return []


def click_captcha_tiles(driver, tile_elements, cell_indices):
    """
    Clicks the CAPTCHA tiles corresponding to the given cell indices.
    
    Args:
        driver: WebDriver instance
        tile_elements: List of tile elements
        cell_indices: List of cell indices to click (0-8)
    """
    if not tile_elements:
        print("Error: No tile elements to click")
        return
    
    try:
        # Sort tiles by position to ensure correct order (top to bottom, left to right)
        tile_elements.sort(key=lambda tile: (tile.location['y'], tile.location['x']))
        
        # Click the tiles for the specified cell indices
        for idx in cell_indices:
            if 0 <= idx < len(tile_elements):
                print(f"Clicking tile at position {idx+1}...")
                ActionChains(driver).move_to_element(tile_elements[idx]).click().perform()
                time.sleep(0.5)  # Small delay between clicks
            else:
                print(f"Warning: Cell index {idx} is out of range")
                
    except Exception as e:
        print(f"Error clicking CAPTCHA tiles: {str(e)}")
        # Fallback to simple clicking if the advanced method fails
        print("Using fallback method to click tiles...")
        for idx in cell_indices:
            if 0 <= idx < len(tile_elements):
                print(f"Clicking tile at position {idx+1} (fallback method)...")
                ActionChains(driver).move_to_element(tile_elements[idx]).click().perform()
                time.sleep(0.5)
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

    # Step 4: GET TARGET NUMBER FROM WEBPAGE
    print("Getting target number from webpage...")
    try:
        # Find the instruction element using multiple approaches
        try:
            instruction_element = driver.find_element(By.CSS_SELECTOR, "#captcha-main-div .box-label")
            instruction_text = instruction_element.text
        except:
            # Alternative approach if the class name is randomized
            instruction_text = driver.execute_script("""
                var container = document.getElementById('captcha-main-div');
                if (container) {
                    var labels = container.querySelectorAll('.box-label');
                    if (labels.length > 0) {
                        return labels[0].textContent;
                    }
                    
                    // Try other common class patterns
                    var divs = container.querySelectorAll('div');
                    for (var i = 0; i < divs.length; i++) {
                        if (divs[i].textContent.includes('Please select all boxes with number')) {
                            return divs[i].textContent;
                        }
                    }
                }
                return '';
            """)
        
        print(f"Instruction text: {instruction_text}")
        
        # Extract target number
        match = re.search(r'\b\d+\b', instruction_text)
        if match:
            target_number = match.group()
            print(f"🎯 Target number detected: {target_number}")
        else:
            print("⚠️ No target number detected in instruction text")
            driver.quit()
            return
    except Exception as e:
        print(f"Error getting instruction text: {str(e)}")
        driver.quit()
        return

    # Step 5: Split image into 3x3 grid and perform OCR in each cell
    print("Splitting image into 3x3 grid and performing OCR on each cell...")
    cells = split_image_grid(cropped_captcha_path, rows=3, cols=3)
    reader = easyocr.Reader(['en'], gpu=False)
    target_cells = ocr_numbers_from_cells(cells, reader, target_number)

    # Print results
    print("\nFinal OCR results:")
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
    print("\nGetting CAPTCHA tile elements from webpage...")
    tile_elements = get_captcha_tiles(driver)
    
    if not tile_elements or len(tile_elements) < 9:
        print("Error: Could not find enough CAPTCHA tiles on the webpage")
        driver.quit()
        return

    # Step 7: Click the tiles that contain the target number
    print(f"\nClicking {len(target_cells)} tiles with the target number...")
    click_captcha_tiles(driver, tile_elements, target_cells)

    # Wait for user to see the result
    input("\nCAPTCHA solving complete. Press Enter to close the browser...")
    driver.quit()


if __name__ == "__main__":
    main()