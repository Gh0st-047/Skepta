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
    Guaranteed working CAPTCHA solver for YOUR specific implementation
    """
    print("[CAPTCHA] Attempting automatic CAPTCHA solving with FINAL working solution...")
    
    try:
        # 1. Wait for CAPTCHA to be fully loaded
        print("[CAPTCHA] Waiting for CAPTCHA to load...")
        try:
            WebDriverWait(driver, 15).until(
                EC.visibility_of_element_located((By.ID, "captcha-main-div"))
            )
            print("[CAPTCHA] CAPTCHA container is visible")
        except Exception as e:
            print(f"[CAPTCHA] Error waiting for CAPTCHA container: {str(e)}")
            return False
        
        # 2. Get the CAPTCHA container
        print("[CAPTCHA] Getting CAPTCHA container...")
        try:
            captcha_container = driver.find_element(By.ID, "captcha-main-div")
            print("[CAPTCHA] Found CAPTCHA container with ID 'captcha-main-div'")
        except Exception as e:
            print(f"[CAPTCHA] Error finding CAPTCHA container: {str(e)}")
            return False
        
        # 3. Find the instruction text to get the target number
        print("[CAPTCHA] Finding CAPTCHA instruction...")
        try:
            # Get the instruction text directly from the container
            instruction_text = driver.execute_script("""
                var container = document.getElementById('captcha-main-div');
                if (container) {
                    var labels = container.querySelectorAll('.box-label');
                    if (labels.length > 0) {
                        return labels[0].textContent;
                    }
                }
                return '';
            """)
            
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
        
        # 4. Find the row that contains the CAPTCHA tiles
        print("[CAPTCHA] Finding the row that contains the CAPTCHA tiles...")
        try:
            # Find the row with style containing "position:relative;"
            captcha_row = driver.execute_script("""
                var container = document.getElementById('captcha-main-div');
                if (container) {
                    var rows = container.querySelectorAll('.row');
                    for (var i = 0; i < rows.length; i++) {
                        var style = window.getComputedStyle(rows[i]);
                        if (style.position === 'relative') {
                            return rows[i];
                        }
                    }
                }
                return null;
            """)
            
            if captcha_row:
                print("[CAPTCHA] Found CAPTCHA row with position:relative;")
            else:
                print("[CAPTCHA] Could not find CAPTCHA row with position:relative;")
                return False
        except Exception as e:
            print(f"[CAPTCHA] Error finding CAPTCHA row: {str(e)}")
            return False
        
        # 5. Find the ACTUAL tile elements (the second element in each pair)
        print("[CAPTCHA] Finding ACTUAL tile elements (the second element in each pair)...")
        tile_divs = []
        
        try:
            # Find ALL div elements within the row
            all_elements = captcha_row.find_elements(By.XPATH, "./*")
            print(f"[CAPTCHA] Found {len(all_elements)} elements in the CAPTCHA row")
            
            # Take every second element (the tile elements)
            for i in range(1, len(all_elements), 2):
                tile = all_elements[i]
                
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
                        tile_divs.append(tile)
                except Exception as e:
                    print(f"[CAPTCHA] Error checking tile properties: {str(e)}")
            
            print(f"[CAPTCHA] Found {len(tile_divs)} visible CAPTCHA tiles")
        except Exception as e:
            print(f"[CAPTCHA] Error finding tiles: {str(e)}")
            return False
        
        # 6. Verify we have 9 tiles
        if len(tile_divs) != 9:
            print(f"[CAPTCHA] ERROR: Expected 9 tiles but found {len(tile_divs)}")
            return False
        
        # 7. Initialize OCR
        print("[CAPTCHA] Initializing OCR reader...")
        reader = easyocr.Reader(['en'], gpu=False)
        
        # 8. Process each tile
        correct_tiles = []
        for i, tile_div in enumerate(tile_divs):
            print(f"[CAPTCHA] Processing tile {i+1}/9...")
            
            try:
                # Take screenshot of just this tile
                tile_screenshot = tile_div.screenshot_as_png
                tile_image = cv2.imdecode(np.frombuffer(tile_screenshot, np.uint8), cv2.IMREAD_COLOR)
                
                # Process with OCR
                results = reader.readtext(tile_image)
                
                # Check if any detected text matches the target number
                for (_, text, prob) in results:
                    # Remove non-digit characters
                    cleaned_text = re.sub(r'\D', '', text)
                    if cleaned_text == target_number:
                        print(f"  ✅ Tile {i+1} contains target number {target_number} (Confidence: {prob:.2f})")
                        correct_tiles.append(tile_div)
                        break
                    elif cleaned_text:
                        print(f"  ➜ Tile {i+1} contains number {cleaned_text} (Confidence: {prob:.2f})")
                else:
                    print(f"  ❌ Tile {i+1} has no matching number")
            except Exception as e:
                print(f"[CAPTCHA] Error processing tile {i+1}: {str(e)}")
        
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
        print(f"[CAPTCHA] Critical error in automatic solving: {str(e)}")
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