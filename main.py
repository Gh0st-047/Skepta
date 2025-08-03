# main.py
import importlib
import time
import attempts
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def setup_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("useAutomationExtension", False)
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => false});")
    return driver


def debug_rsp_data(driver):
    """Dump rspData to understand why form isn't validating"""
    rsp_data = driver.execute_script("return JSON.stringify(rspData, null, 2);")
    print(f"\n🔍 rspData contents:\n{rsp_data}")
    
    # Check specific field
    location_status = driver.execute_script("""
        var locationId = $('label:contains("Location*")').nextAll('[data-role="dropdownlist"]').first().attr('id');
        var item = rspData.find(x => x.Id === locationId);
        return item ? 
            `Location: Selected=${item.Selected}, Time=${item.Total}ms` : 
            'Location: NOT TRACKED';
    """)
    print(f"📍 {location_status}")



def main():
    print("🚀 Visa Automation Hot-Reload System")
    print("👉 Step 1: Manually log in and navigate to the appointment form.")
    print("✅ Once there, press ENTER to start the automation loop.")

    driver = setup_driver()
    driver.get("https://appointment.theitalyvisa.com")

    input("\nPress ENTER when you are on the target form...")

    print("\n🔁 Automation loop started. Press ENTER to reload and retry.")

    while True:
        try:
            input("🔁 Press ENTER to reload attempts.py and run... (Ctrl+C to exit)")
            importlib.reload(attempts)  # Reload your changes
            attempts.run(driver)
            debug_rsp_data(driver)

        except KeyboardInterrupt:
            print("\n👋 Exiting. Browser will close.")
            break
        except Exception as e:
            print(f"💥 Unexpected error: {e}")
            continue

    driver.quit()

if __name__ == "__main__":
    main()