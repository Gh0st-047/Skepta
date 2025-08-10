import time
import random
import cv2
import numpy as np
import re
import easyocr
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import selenium_stealth


# === CONFIGURATION ===
EMAIL = "justarandomemail785@gmail.com"
PASSWORD = "Password11#"

# Coordinate-based actions (ONLY for the final 3 locations as requested)
NOTIF_CLOSE_X, NOTIF_CLOSE_Y = 342, 105
ARROW_X, ARROW_Y = 204, 15
BOOK_NOW_X, BOOK_NOW_Y = 246, 120


def setup_driver():
    """Set up a stealthy Chrome driver with proper mobile emulation"""
    mobile_emulation = {
        "deviceMetrics": {"width": 375, "height": 812, "pixelRatio": 3.0},
        "userAgent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_6 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/15.6 Mobile/15E148 Safari/604.1"
        )
    }
    
    options = Options()
    options.add_argument("--incognito")
    options.add_experimental_option("mobileEmulation", mobile_emulation)
    
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-infobars")
    options.add_argument("--window-position=0,0")
    options.add_argument("--disable-setuid-sandbox")
    
    options.add_argument(f"--window-size={370 + random.randint(0,10)},{810 + random.randint(0,10)}")
    
    driver = webdriver.Chrome(options=options)
    
    driver.execute_script("""
        Object.defineProperty(navigator, 'webdriver', {
          get: () => undefined
        })
    """)
    
    try:
        selenium_stealth.hide_navigator_webdriver(driver)
        selenium_stealth.hide_navigator_permissions(driver)
        selenium_stealth.hide_navigator_plugins(driver)
        selenium_stealth.hide_window_outerdimensions(driver)
    except:
        pass
    
    return driver

def wait_for_page_ready(driver):
    """Wait for all page initialization to complete"""
    print("[WAIT] Waiting for page to be fully initialized...")
    
    WebDriverWait(driver, 30).until(
        lambda d: d.execute_script('return document.readyState === "complete"')
    )
    
    try:
        WebDriverWait(driver, 10).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, ".preloader"))
        )
        print("[READY] Preloader disappeared")
    except:
        pass
    
    try:
        WebDriverWait(driver, 15).until(
            EC.invisibility_of_element_located((By.ID, "global-overlay"))
        )
        print("[READY] Global overlay disappeared")
    except Exception as e:
        print(f"[WARNING] Global overlay still present: {str(e)}")
    
    time.sleep(3)

def find_visible_email_field(driver):
    """Find the ONLY visible email field without relying on hardcoded IDs"""
    print("[FIND] Locating the visible email field...")
    
    all_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'][autocomplete='off']")
    
    for field in all_inputs:
        try:
            if field.is_displayed() and field.size['height'] > 0 and field.size['width'] > 0:
                is_covered = driver.execute_script("""
                    var elem = arguments[0];
                    var bounding = elem.getBoundingClientRect();
                    var elementAtPoint = document.elementFromPoint(
                        bounding.left + bounding.width/2,
                        bounding.top + bounding.height/2
                    );
                    return elementAtPoint !== elem && !elem.contains(elementAtPoint);
                """, field)
                
                if not is_covered:
                    print(f"[FOUND] Visible email field with ID: {field.get_attribute('id')}")
                    return field
        except:
            continue
    
    visible_field_id = driver.execute_script("""
        var inputs = document.querySelectorAll("input[type='text'][autocomplete='off']");
        for (var i = 0; i < inputs.length; i++) {
            var el = inputs[i];
            var style = window.getComputedStyle(el);
            if (style.display !== 'none' && 
                style.visibility !== 'hidden' && 
                el.offsetWidth > 0 && 
                el.offsetHeight > 0) {
                return el.id;
            }
        }
        return null;
    """)
    
    if visible_field_id:
        visible_field = driver.find_element(By.ID, visible_field_id)
        print(f"[FOUND via JS] Visible email field: #{visible_field_id}")
        return visible_field
    
    raise Exception("[ERROR] No visible email field found. Bot protection triggered.")

def find_verify_button(driver):
    """Find the Verify button"""
    print("[FIND] Locating Verify button...")
    
    try:
        verify_btn = driver.find_element(By.XPATH, "//button[contains(., 'Verify')]")
        if verify_btn.is_displayed():
            print("[FOUND] Verify button by text content")
            return verify_btn
    except:
        pass
    
    try:
        verify_btn = driver.find_element(By.ID, "btnVerify")
        if verify_btn.is_displayed():
            print("[FOUND] Verify button by ID")
            return verify_btn
    except:
        pass
    
    verify_btn_id = driver.execute_script("""
        var buttons = document.querySelectorAll("button");
        for (var i = 0; i < buttons.length; i++) {
            var btn = buttons[i];
            if ((btn.textContent.includes('Verify') || btn.innerText.includes('Verify')) &&
                window.getComputedStyle(btn).display !== 'none') {
                return btn.id;
            }
        }
        return null;
    """)
    
    if verify_btn_id:
        verify_btn = driver.find_element(By.ID, verify_btn_id)
        print(f"[FOUND via JS] Verify button: #{verify_btn_id}")
        return verify_btn
    
    raise Exception("[ERROR] Could not locate Verify button")

def find_password_field(driver):
    """Find the password field"""
    print("[FIND] Locating password field...")
    
    selectors = [
        "input[type='password']",
        ".fakepassword",
        "input.entry-disabled[type='text']"
    ]
    
    for selector in selectors:
        try:
            pwd_field = driver.find_element(By.CSS_SELECTOR, selector)
            if pwd_field.is_displayed():
                print(f"[FOUND] Password field using selector: {selector}")
                return pwd_field
        except:
            continue
    
    pwd_field_id = driver.execute_script("""
        var inputs = document.querySelectorAll("input[type='password'], .fakepassword, input.entry-disabled");
        for (var i = 0; i < inputs.length; i++) {
            var el = inputs[i];
            if (window.getComputedStyle(el).display !== 'none' && el.offsetWidth > 0) {
                return el.id;
            }
        }
        return null;
    """)
    
    if pwd_field_id:
        pwd_field = driver.find_element(By.ID, pwd_field_id)
        print(f"[FOUND via JS] Password field: #{pwd_field_id}")
        return pwd_field
    
    raise Exception("[ERROR] Could not locate password field")

def find_submit_button(driver):
    """Find the submit/login button"""
    print("[FIND] Locating submit button...")
    
    try:
        submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
        if submit_btn.is_displayed():
            print("[FOUND] Submit button by type")
            return submit_btn
    except:
        pass
    
    try:
        submit_btn = driver.find_element(By.XPATH, "//button[contains(., 'Submit') or contains(., 'Login')]")
        if submit_btn.is_displayed():
            print("[FOUND] Submit button by text content")
            return submit_btn
    except:
        pass
    
    submit_btn_id = driver.execute_script("""
        var buttons = document.querySelectorAll("button");
        for (var i = 0; i < buttons.length; i++) {
            var btn = buttons[i];
            if ((btn.textContent.includes('Submit') || btn.innerText.includes('Login')) &&
                window.getComputedStyle(btn).display !== 'none') {
                return btn.id;
            }
        }
        return null;
    """)
    
    if submit_btn_id:
        submit_btn = driver.find_element(By.ID, submit_btn_id)
        print(f"[FOUND via JS] Submit button: #{submit_btn_id}")
        return submit_btn
    
    raise Exception("[ERROR] Could not locate submit button")

def human_like_type(element, text, driver):
    """Simulate human-like typing"""
    print(f"[TYPE] Entering text with human-like typing...")
    ActionChains(driver).move_to_element(element).click().perform()
    time.sleep(0.3)
    element.clear()
    time.sleep(0.2)
    
    for char in text:
        element.send_keys(char)
        time.sleep(0.1 + random.random() * 0.2)
    
    driver.execute_script("""
        var evt = new Event('input', { bubbles: true });
        arguments[0].dispatchEvent(evt);
        var changeEvt = new Event('change', { bubbles: true });
        arguments[0].dispatchEvent(changeEvt);
    """, element)
    
    entered_value = driver.execute_script("return arguments[0].value;", element)
    if entered_value != text:
        driver.execute_script("arguments[0].value = arguments[1];", element, text)
        driver.execute_script("""
            var evt = new Event('input', { bubbles: true });
            arguments[0].dispatchEvent(evt);
        """, element)
    
    time.sleep(0.5)

def click_element(element, driver):
    """Click an element"""
    print(f"[CLICK] Clicking element with ID: {element.get_attribute('id') or 'unknown'}")
    driver.execute_script("""
        var element = arguments[0];
        var rect = element.getBoundingClientRect();
        var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        var targetScroll = (rect.top + scrollTop) - (window.innerHeight / 2);
        window.scrollTo({
            top: targetScroll,
            behavior: 'smooth'
        });
    """, element)
    
    time.sleep(1.5)
    ActionChains(driver).move_to_element(element).pause(random.uniform(0.3, 0.7)).click().perform()
    time.sleep(1)

def click_at(x, y, label="", driver=None):
    """Click at specific coordinates with human-like behavior (ONLY for final 3 locations)"""
    if driver is None:
        return
    
    print(f"[CLICK] Clicking {label} at ({x}, {y})")
    
    # Move mouse to position with human-like movement
    driver.execute_script("""
        var x = arguments[0];
        var y = arguments[1];
        var el = document.elementFromPoint(x, y);
        if (el) {
            el.scrollIntoView({block: 'center', behavior: 'smooth'});
            // Create mouse movement effect
            var rect = el.getBoundingClientRect();
            var centerX = rect.left + rect.width/2;
            var centerY = rect.top + rect.height/2;
            
            // Move mouse to random position near target first
            var offsetX = Math.random() * 20 - 10;
            var offsetY = Math.random() * 20 - 10;
            var startX = centerX + offsetX;
            var startY = centerY + offsetY;
            
            // Create mouse movement events
            var moveEvent = new MouseEvent('mousemove', {
                view: window,
                bubbles: true,
                cancelable: true,
                clientX: startX,
                clientY: startY
            });
            document.elementFromPoint(startX, startY).dispatchEvent(moveEvent);
            
            // Small pause
            setTimeout(function() {
                var clickEvent = new MouseEvent('click', {
                    view: window,
                    bubbles: true,
                    cancelable: true,
                    clientX: x,
                    clientY: y
                });
                el.dispatchEvent(clickEvent);
            }, 200 + Math.random() * 300);
        }
    """, x, y)
    
    # Wait for action to complete
    time.sleep(1.5 + random.random())

def check_captcha_error(driver):
    """
    Check if CAPTCHA error is displayed using the site's actual implementation.
    """
    print("[ERROR CHECK] Checking for CAPTCHA error...")
    
    # Method 1: Check if URL contains error parameter
    try:
        if "err=" in driver.current_url:
            print("[ERROR] URL contains error parameter")
            return True
    except:
        pass
    
    # Method 2: Check for the specific error element
    try:
        error_element = driver.find_element(By.XPATH, "/html/body/div/div[2]/div[1]")
        if error_element.is_displayed() and "Invalid captcha selection" in error_element.text:
            print(f"[ERROR] Found CAPTCHA error: '{error_element.text}'")
            return True
    except:
        pass
    
    # Method 3: Check for validation summary errors
    try:
        validation_summary = driver.find_element(By.CSS_SELECTOR, ".validation-summary:not(.validation-summary-valid)")
        if validation_summary.is_displayed() and "captcha" in validation_summary.text.lower():
            print(f"[ERROR] Found CAPTCHA error in validation summary: {validation_summary.text}")
            return True
    except:
        pass
    
    print("[CHECK] No CAPTCHA error detected")
    return False
def solve_captcha_automatically(driver):
    """
    Automatically solve the CAPTCHA by taking one screenshot of the entire CAPTCHA area
    Returns True if solved, False if manual solving is needed
    """
    print("[CAPTCHA] Attempting automatic CAPTCHA solving with reliable approach...")
    
    try:
        # 1. Find the instruction text to get the target number
        print("[CAPTCHA] Finding CAPTCHA instruction...")
        try:
            # Look for the instruction element - this is the most reliable part
            instruction_element = driver.find_element(By.CSS_SELECTOR, "div.box-label")
            instruction_text = instruction_element.text
            print(f"[CAPTCHA] Instruction: {instruction_text}")
            
            # Extract target number
            match = re.search(r'\b\d+\b', instruction_text)
            if match:
                target_number = match.group()
                print(f"[CAPTCHA] Target number: {target_number}")
            else:
                print("[CAPTCHA] Could not find target number in instruction")
                return False
        except Exception as e:
            print(f"[CAPTCHA] Error getting instruction: {str(e)}")
            return False
        
        # 2. Find ALL tile elements (critical fix - use the actual onclick pattern)
        print("[CAPTCHA] Finding tile elements...")
        # This selector finds elements with onclick="Select('id',this)"
        tile_divs = driver.find_elements(By.XPATH, "//div[contains(@onclick, 'Select(')]")
        
        if len(tile_divs) == 0:
            # Alternative selector based on your HTML structure
            tile_divs = driver.find_elements(By.CSS_SELECTOR, "div.col-4 > div[style*='padding:5px;'][id]")
        
        if len(tile_divs) == 0:
            # One more attempt with a broader selector
            tile_divs = driver.find_elements(By.CSS_SELECTOR, "div.col-4 > div[id]")
        
        print(f"[CAPTCHA] Found {len(tile_divs)} tile elements")
        
        # We need exactly 9 tiles for a 3x3 grid
        if len(tile_divs) < 9:
            print(f"[CAPTCHA] Warning: Expected 9 tiles but found {len(tile_divs)}")
            return False
        
        # 3. Take a screenshot of the ENTIRE viewport
        print("[CAPTCHA] Taking full viewport screenshot...")
        screenshot = driver.get_screenshot_as_png()
        screenshot = cv2.imdecode(np.frombuffer(screenshot, np.uint8), cv2.IMREAD_COLOR)
        
        # Get viewport dimensions
        viewport_width = driver.execute_script("return window.innerWidth;")
        viewport_height = driver.execute_script("return window.innerHeight;")
        print(f"[CAPTCHA] Viewport dimensions: {viewport_width}x{viewport_height}")
        
        # 4. Calculate the bounding box that contains all tiles
        min_x, min_y = viewport_width, viewport_height
        max_x, max_y = 0, 0
        
        # Store tile positions for later
        tile_positions = []
        
        for i, tile_div in enumerate(tile_divs):
            try:
                # Get the tile's position and size
                location = tile_div.location
                size = tile_div.size
                
                # Calculate absolute coordinates
                x = location['x']
                y = location['y']
                w = size['width']
                h = size['height']
                
                # Update bounding box
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x + w)
                max_y = max(max_y, y + h)
                
                # Store position for later mapping
                tile_positions.append((i, x, y, w, h))
                
                print(f"[CAPTCHA] Tile {i+1} at ({x}, {y}) size ({w}x{h})")
            except Exception as e:
                print(f"[CAPTCHA] Error getting tile {i+1} position: {str(e)}")
        
        # Calculate the CAPTCHA area dimensions
        captcha_width = max_x - min_x
        captcha_height = max_y - min_y
        
        print(f"[CAPTCHA] Calculated CAPTCHA area: ({min_x}, {min_y}) to ({max_x}, {max_y})")
        print(f"[CAPTCHA] Dimensions: {captcha_width}x{captcha_height}")
        
        # 5. Crop the screenshot to just the CAPTCHA area
        captcha_area = screenshot[int(min_y):int(max_y), int(min_x):int(max_x)]
        
        # Save for debugging (optional)
        # cv2.imwrite("captcha_area.png", captcha_area)
        
        # 6. Initialize OCR
        print("[CAPTCHA] Initializing OCR reader...")
        reader = easyocr.Reader(['en'], gpu=False)
        
        # 7. Split into 3x3 grid based on the actual tile positions
        print("[CAPTCHA] Processing tiles in grid...")
        
        # Sort tiles by position to create a grid
        # First sort by Y position (rows), then by X position (columns)
        sorted_tiles = sorted(tile_positions, key=lambda pos: (pos[2], pos[1]))
        
        # Now organize into a 3x3 grid
        grid = []
        current_row = []
        prev_y = None
        
        for i, x, y, w, h in sorted_tiles:
            if prev_y is None or abs(y - prev_y) < h/2:
                current_row.append((i, x, y, w, h))
            else:
                grid.append(current_row)
                current_row = [(i, x, y, w, h)]
            prev_y = y
        
        if current_row:
            grid.append(current_row)
        
        # Ensure we have a 3x3 grid
        if len(grid) != 3 or any(len(row) != 3 for row in grid):
            print(f"[CAPTCHA] Warning: Grid structure is {len(grid)}x{len(grid[0]) if grid else 0}, not 3x3")
            # Try to force a 3x3 grid
            all_tiles = [tile for row in grid for tile in row]
            grid = [all_tiles[i:i+3] for i in range(0, 9, 3)]
        
        # 8. Process each tile in the grid
        correct_tiles = []
        for row_idx, row in enumerate(grid):
            for col_idx, (tile_idx, x, y, w, h) in enumerate(row):
                # Get the tile element
                tile_div = tile_divs[tile_idx]
                
                # Calculate position relative to the CAPTCHA area
                rel_x = x - min_x
                rel_y = y - min_y
                
                # Extract the tile from the CAPTCHA area image
                tile_img = captcha_area[int(rel_y):int(rel_y+h), int(rel_x):int(rel_x+w)]
                
                # Process with OCR
                results = reader.readtext(tile_img)
                
                # Check if any detected text matches the target number
                found_match = False
                for (_, text, prob) in results:
                    # Remove non-digit characters
                    cleaned_text = re.sub(r'\D', '', text)
                    if cleaned_text == target_number and prob > 0.5:
                        print(f"  ✅ Grid position ({row_idx},{col_idx}) contains target number {target_number} (Confidence: {prob:.2f})")
                        correct_tiles.append(tile_div)
                        found_match = True
                        break
                    elif cleaned_text and prob > 0.5:
                        print(f"  ➜ Grid position ({row_idx},{col_idx}) contains number {cleaned_text} (Confidence: {prob:.2f})")
                
                if not found_match:
                    print(f"  ❌ Grid position ({row_idx},{col_idx}) has no matching number")
        
        # 9. Click the correct tiles
        if correct_tiles:
            print(f"[CAPTCHA] Clicking {len(correct_tiles)} correct tiles...")
            for i, tile_div in enumerate(correct_tiles):
                print(f"[CAPTCHA] Clicking tile {i+1}...")
                click_element(tile_div, driver)
                time.sleep(0.7)  # Small delay between clicks
            return True
        else:
            print("[CAPTCHA] No correct tiles found")
            return False
            
    except Exception as e:
        print(f"[CAPTCHA] Error in automatic solving: {str(e)}")
        return False

def main():
    driver = None
    try:
        print("[SETUP] Initializing stealthy Chrome driver...")
        driver = setup_driver()
        wait = WebDriverWait(driver, 25)
        
        print("[NAVIGATE] Opening login page...")
        driver.get("https://appointment.theitalyvisa.com/Global/account/login")
        
        wait_for_page_ready(driver)
        
        print("[EMAIL] Locating and filling email field...")
        email_field = find_visible_email_field(driver)
        driver.execute_script("arguments[0].focus();", email_field)
        time.sleep(0.5)
        human_like_type(email_field, EMAIL, driver)
        
        print("[VERIFY] Locating and clicking Verify button...")
        verify_btn = find_verify_button(driver)
        click_element(verify_btn, driver)
        
        time.sleep(2)
        if "bot" in driver.current_url:
            raise Exception("[FATAL] Bot detection triggered!")
        
        # === CAPTCHA HANDLING ===
        print("[CAPTCHA] CAPTCHA page loaded")
        
        # Wait for CAPTCHA to fully load
        time.sleep(3)
        
        # Try automatic solving first
        auto_solved = solve_captcha_automatically(driver)
        
        if not auto_solved:
            print("[CAPTCHA] Automatic solving failed, falling back to manual solving")
            input("[PAUSE] Solve the CAPTCHA manually, then press Enter to continue...")
        else:
            print("[CAPTCHA] CAPTCHA solved automatically!")
        
        # CAPTCHA handling loop for cases where automatic/manual solving was incorrect
        print(f"[CAPTCHA] Starting CAPTCHA handling loop...")
        login_successful = False
        
        while not login_successful:
            # Find password field and enter password
            print("[PASSWORD] Locating and filling password field...")
            password_field = find_password_field(driver)
            human_like_type(password_field, PASSWORD, driver)
            
            # Click submit button
            print("[SUBMIT] Locating and clicking submit button...")
            submit_btn = find_submit_button(driver)
            driver.execute_script("arguments[0].click();", submit_btn)
            
            # Wait for server response
            print("[WAIT] Waiting for server response...")
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script('return document.readyState === "complete"')
            )
            time.sleep(3)
            
            # Check if we're still on the CAPTCHA page
            if "/Global/NewCaptcha/LoginCaptcha" in driver.current_url:
                # Check for CAPTCHA error message
                if check_captcha_error(driver):
                    print("[CAPTCHA] CAPTCHA was incorrect, retrying...")
                    
                    # Try automatic solving again if we're retrying
                    auto_solved = solve_captcha_automatically(driver)
                    if not auto_solved:
                        input("[PAUSE] CAPTCHA was incorrect. Solve the CAPTCHA manually, then press Enter to continue...")
                else:
                    # This might be a different error
                    print("[ERROR] Login failed with unknown error")
                    input("[PAUSE] Please check the error and press Enter to continue...")
            else:
                # We've successfully moved to a different page
                print("[SUCCESS] Login successful! Redirected to:", driver.current_url)
                login_successful = True
        
        # Wait for navigation to complete
        time.sleep(2)
        
        # === FINAL STEPS (USING COORDINATES AS REQUESTED) ===
        print("[FINAL] Completing login process...")
        
        # Click notification close
        click_at(NOTIF_CLOSE_X, NOTIF_CLOSE_Y, "Notification Close", driver=driver)
        
        # Click arrow
        click_at(ARROW_X, ARROW_Y, "Arrow", driver=driver)
        
        # Click Book Now
        click_at(BOOK_NOW_X, BOOK_NOW_Y, "Book Now", driver=driver)
        
        print("[SUCCESS] Automation completed successfully!")
        time.sleep(5)
        
    except Exception as e:
        print(f"[ERROR] Automation failed: {str(e)}")
        input("[PAUSE] Press Enter to close the browser...")
    finally:
        if driver:
            print("[CLEANUP] Closing browser...")
            driver.quit()

if __name__ == "__main__":
    main()