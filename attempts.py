# attempts.py
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ATTEMPT").info

def human_delay(min_seconds=0.7, max_seconds=1.8):
    """Random delay to mimic human interaction"""
    delay = min_seconds + (random.random() * (max_seconds - min_seconds))
    time.sleep(delay)

def find_dropdown_by_label(driver, label_text):
    """Find Kendo dropdown by label text (survives randomized IDs and class names)"""
    return driver.execute_script("""
        var labelText = arguments[0];
        // Find label with flexible matching (handles extra spaces)
        var $label = $('label').filter(function() {
            return $(this).text().trim().replace(/\\s+/g, ' ') === labelText;
        });
        
        if ($label.length === 0) {
            console.error('Label not found:', labelText);
            return null;
        }
        
        // Find the associated dropdown input
        var $dropdown = $label.nextAll('input[data-role="dropdownlist"]').first();
        if ($dropdown.length === 0) {
            // Try alternative approach: find in the same form group
            $dropdown = $label.closest('.mb-3, .form-group').find('input[data-role="dropdownlist"]');
        }
        
        if ($dropdown.length === 0) {
            console.error('Dropdown input not found for label:', labelText);
            return null;
        }
        
        return $dropdown.attr('id');
    """, label_text)

def verify_rsp_data(driver, field_name, expected_value=None):
    """Check if rspData properly recorded the interaction"""
    result = driver.execute_script("""
        var label = arguments[0];
        var expectedValue = arguments[1];
        
        // Find the label with flexible matching
        var $label = $('label').filter(function() {
            return $(this).text().trim().replace(/\\s+/g, ' ') === label;
        });
        
        if ($label.length === 0) {
            return { 
                valid: false, 
                message: "Label not found", 
                details: { label: label }
            };
        }
        
        // Find the dropdown input
        var $dropdown = $label.nextAll('input[data-role="dropdownlist"]').first();
        if ($dropdown.length === 0) {
            $dropdown = $label.closest('.mb-3, .form-group').find('input[data-role="dropdownlist"]');
        }
        
        if ($dropdown.length === 0) {
            return { 
                valid: false, 
                message: "Dropdown not found", 
                details: { label: label }
            };
        }
        
        var id = $dropdown.attr('id');
        var item = rspData.find(x => x.Id === id);
        
        if (!item) {
            return { 
                valid: false, 
                message: "No rspData entry",
                details: {
                    label: label,
                    id: id,
                    rspData: JSON.stringify(rspData)
                }
            };
        }
        
        var isValid = item.Selected && item.End !== null && item.Total > 300;
        var message = isValid ? 
            "rspData validated" : 
            `rspData invalid: Selected=${item.Selected}, End=${item.End}, Total=${item.Total}`;
            
        return { 
            valid: isValid, 
            message: message,
            details: {
                label: label,
                id: id,
                start: item.Start,
                end: item.End,
                total: item.Total,
                selected: item.Selected
            }
        };
    """, field_name, expected_value)
    
    if result["valid"]:
        log(f"✅ rspData validated for '{field_name}'")
    else:
        log(f"⚠️ {result['message']} for '{field_name}'")
        if "details" in result:
            log(f"🔍 rspData details: {result['details']}")
    
    return result["valid"]

def select_dropdown_humanlike(driver, label_text, visible_text):
    log(f"🎯 Selecting '{visible_text}' in '{label_text}'")
    
    # 1. Find the dropdown ID using label
    dropdown_id = find_dropdown_by_label(driver, label_text)
    if not dropdown_id:
        log(f"❌ Could not find dropdown for label '{label_text}'")
        # Try to debug why
        labels = driver.execute_script("""
            return $('label').map(function() { 
                return $(this).text().trim().replace(/\\s+/g, ' '); 
            }).get();
        """)
        log(f"🔍 Available labels: {labels}")
        raise Exception(f"Dropdown not found for label '{label_text}'")
    
    log(f"🔍 Found dropdown ID: {dropdown_id}")
    
    # 2. Open the dropdown (triggers onDrpOpen)
    log(f"⏳ Waiting for dropdown to open...")
    driver.execute_script(f"""
        var ddl = $('#{dropdown_id}').data('kendoDropDownList');
        if (ddl) {{
            ddl.open();
            console.log('Dropdown opened for {dropdown_id}');
        }} else {{
            console.error('Kendo widget not found for #{dropdown_id}');
        }}
    """)
    human_delay(0.8, 1.2)
    
    # 3. Wait for data to bind (critical with autoBind: false)
    log("⏳ Waiting for dropdown data to bind...")
    data_bound = driver.execute_script(f"""
        var ddl = $('#{dropdown_id}').data('kendoDropDownList');
        return ddl && ddl.dataSource && ddl.dataSource.data && ddl.dataSource.data().length > 0;
    """)
    
    if not data_bound:
        start_time = time.time()
        while time.time() - start_time < 5:
            data_bound = driver.execute_script(f"""
                var ddl = $('#{dropdown_id}').data('kendoDropDownList');
                return ddl && ddl.dataSource && ddl.dataSource.data && ddl.dataSource.data().length > 0;
            """)
            if data_bound:
                break
            time.sleep(0.3)
    
    if not data_bound:
        log("❌ Dropdown data never bound")
        # Dump the dataSource structure for debugging
        data_info = driver.execute_script(f"""
            var ddl = $('#{dropdown_id}').data('kendoDropDownList');
            if (!ddl || !ddl.dataSource) return 'No dataSource';
            return 'dataSource exists, data: ' + (ddl.dataSource.data ? ddl.dataSource.data().length : 'no data method');
        """)
        log(f"🔍 DataSource info: {data_info}")
        raise Exception(f"Dropdown data failed to bind for '{label_text}'")
    
    # 4. Find the item by text and select it (triggers onDrpSelect)
    log(f"🔍 Finding '{visible_text}' in dropdown options...")
    selected = driver.execute_script(f"""
        var ddl = $('#{dropdown_id}').data('kendoDropDownList');
        var found = false;
        var itemId = null;
        
        if (!ddl) {{
            console.error('Kendo widget not found for #{dropdown_id}');
            return {{ found: false, itemId: null }};
        }}
        
        ddl.ul.find('li').each(function() {{
            var text = $(this).text().trim();
            if (text === '{visible_text}') {{
                ddl.select(this);
                found = true;
                itemId = $(this).data('uid');
                return false;  // break
            }}
        }});
        
        // If exact match not found, try case-insensitive
        if (!found) {{
            ddl.ul.find('li').each(function() {{
                var text = $(this).text().trim().toLowerCase();
                if (text === '{visible_text.lower()}') {{
                    ddl.select(this);
                    found = true;
                    itemId = $(this).data('uid');
                    return false;
                }}
            }});
        }}
        
        return {{ found: found, itemId: itemId }};
    """)
    
    if not selected["found"]:
        # Try to dump available options for debugging
        options = driver.execute_script(f"""
            var ddl = $('#{dropdown_id}').data('kendoDropDownList');
            if (!ddl || !ddl.ul) return [];
            return ddl.ul.find('li').map(function() {{ 
                return $(this).text().trim(); 
            }}).get();
        """)
        log(f"❌ Item '{visible_text}' not found in '{label_text}'")
        log(f"🔍 Available options: {options}")
        raise Exception(f"Item '{visible_text}' not found in '{label_text}'")
    
    log(f"✅ Found item with ID: {selected['itemId']}")
    
    # 5. Wait for selection to process (critical for rspData)
    human_delay(0.7, 1.3)
    
    # 6. CRITICAL FIX: Instead of programmatically closing,
    #    click outside the dropdown to trigger onDrpClose properly
    log("⏳ Waiting for onDrpClose to trigger...")
    
    # Click on the label (safe area outside dropdown)
    driver.execute_script(f"""
        var label = $('label:contains("{label_text}")')[0];
        if (label) {{
            label.click();
            console.log('Clicked outside dropdown to trigger onDrpClose');
        }}
    """)
    
    # Give time for onDrpClose to process
    human_delay(0.5, 0.8)
    
    # 7. Verify selection was recorded in rspData with proper timing
    is_valid = verify_rsp_data(driver, label_text, visible_text)
    
    # 8. Double-check the UI shows the correct selection
    actual_text = driver.execute_script(f"""
        var ddl = $('#{dropdown_id}').data('kendoDropDownList');
        return ddl ? ddl.text() : 'Dropdown not found';
    """)
    
    if actual_text != visible_text:
        log(f"⚠️ UI shows '{actual_text}' but expected '{visible_text}'")
    else:
        log(f"✅ UI confirms selection: '{actual_text}'")
    
    return is_valid

def get_applicant_id_suffix(driver):
    """Extract the dynamic suffix used in radio button IDs (e.g., 'qxktoopp')"""
    return driver.execute_script("""
        // Look for any radio button with name starting with 'af'
        var radio = $('input[name^="af"][value="Individual"]');
        if (radio.length > 0) {
            // Extract the suffix from the ID (e.g., from 'selfqxktoopp' get 'qxktoopp')
            var id = radio.attr('id');
            if (id && id.startsWith('self')) {
                return id.substring(4);
            }
        }
        
        // Try alternative approach: look at onclick handler
        var onclick = $('input[name^="af"]').attr('onclick');
        if (onclick) {
            var match = onclick.match(/OnAppointmentForChange\\(event,'([^']+)'/);
            if (match && match[1]) {
                return match[1];
            }
        }
        
        return null;
    """)

def select_radio_by_value(driver, value):
    """Select radio button by value with proper event triggering"""
    log(f"🎯 Selecting radio: '{value}'")
    
    # 1. Find the dynamic suffix used in IDs
    suffix = get_applicant_id_suffix(driver)
    if not suffix:
        # Try to dump all relevant elements for debugging
        debug_info = driver.execute_script("""
            var radios = $('input[name^="af"]').map(function() {
                return {
                    id: this.id,
                    name: this.name,
                    value: this.value,
                    onclick: this.getAttribute('onclick')
                };
            }).get();
            return radios;
        """)
        log(f"🔍 Radio button debug info: {debug_info}")
        raise Exception("Could not determine applicant ID suffix")
    
    log(f"🔍 Found applicant ID suffix: {suffix}")
    
    # 2. Construct the correct element IDs
    element_id = f"self{suffix}" if value == "Individual" else f"family{suffix}"
    
    # 3. Use JavaScript to properly trigger the change event
    success = driver.execute_script(f"""
        try {{
            // Find the radio button
            var radio = $('#{element_id}');
            if (radio.length === 0) {{
                console.error('Radio button not found:', '#{element_id}');
                return false;
            }}
            
            // Check if it's already selected
            if (radio.prop('checked')) {{
                console.log('Radio already selected:', '#{element_id}');
                return true;
            }}
            
            // Set checked property
            radio.prop('checked', true);
            
            // Trigger the custom change handler
            OnAppointmentForChange(null, '{suffix}');
            
            // Force a small delay to allow processing
            setTimeout(function() {{
                radio.trigger('change');
            }}, 100);
            
            console.log('Appointment for set to:', '{value}');
            return true;
        }} catch (e) {{
            console.error('Error selecting radio:', e);
            return false;
        }}
    """)
    
    if not success:
        raise Exception(f"Failed to select radio value '{value}'")
    
    human_delay(0.5, 1.0)
    
    # 4. Verify the selection
    is_selected = driver.execute_script(f"""
        return $('#self{suffix}').prop('checked');
    """)
    
    if is_selected:
        log(f"✅ Successfully selected radio: '{value}'")
        return True
    else:
        log(f"❌ Radio '{value}' is not checked after selection")
        return False

def handle_modal(driver, modal_id):
    """Handle confirmation modals with human-like delays"""
    try:
        # Wait for modal to appear
        WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.ID, modal_id))
        )
        log(f"🔍 Modal '{modal_id}' detected")
        human_delay(0.5, 1.0)
        
        # Click confirm button
        btn = driver.find_element(By.CSS_SELECTOR, f"#{modal_id} .btn-primary")
        driver.execute_script("arguments[0].click();", btn)
        
        # Wait for modal to close
        WebDriverWait(driver, 3).until(
            EC.invisibility_of_element_located((By.ID, modal_id))
        )
        log(f"✅ Confirmed modal: {modal_id}")
        return True
    except Exception as e:
        log(f"ℹ️ Modal '{modal_id}' not present or already closed")
        return False

def verify_form_state(driver):
    """Comprehensive check if form is actually ready to submit"""
    required_fields = [
        "Appointment For*",
        "Location*",
        "Visa Type*",
        "Visa Sub Type*",
        "Category*"
    ]
    
    all_valid = True
    for field in required_fields:
        is_valid = verify_rsp_data(driver, field)
        if not is_valid:
            all_valid = False
            log(f"❌ Field '{field}' failed validation")
    
    # Check if Next button is enabled
    try:
        next_btn = driver.find_element(By.XPATH, "//button[contains(., 'Next') or contains(., 'Continue')]")
        is_enabled = not next_btn.get_attribute("disabled")
        if is_enabled:
            log("🟢 Next button is ENABLED - form is ready to submit!")
        else:
            log("🟡 Next button is DISABLED - form not ready")
            all_valid = False
    except Exception as e:
        log(f"🔍 Could not find Next button: {str(e)}")
        all_valid = False
    
    return all_valid

def run(driver):
    log("Starting automation...")
    start_time = time.time()
    
    try:
        # === 1. APPOINTMENT FOR (MUST BE FIRST) ===
        log("🎯 Selecting 'Appointment For' FIRST as required by the flow")
        if not select_radio_by_value(driver, "Individual"):
            return False
        human_delay(1.0, 1.5)
        
        # === 2. LOCATION ===
        if not select_dropdown_humanlike(driver, "Location*", "Karachi"):
            return False
        handle_modal(driver, "LocationConfirmModel")
        human_delay(2.5, 3.5)  # Critical: wait for filtering to complete
        
        # === 3. VISA TYPE ===
        if not select_dropdown_humanlike(driver, "Visa Type*", "National / Schengen Visa"):
            return False
        human_delay(2.0, 3.0)  # Must wait for subtype filtering
        
        # === 4. VISA SUB TYPE ===
        if not select_dropdown_humanlike(driver, "Visa Sub Type*", "Business Visa"):
            return False
        human_delay(1.0, 1.5)
        
        # === 5. CATEGORY ===
        if not select_dropdown_humanlike(driver, "Category*", "Premium"):
            return False
        handle_modal(driver, "PremiumTypeModel")
        
        # === FINAL VALIDATION ===
        success = verify_form_state(driver)
        log(f"⏱️ Total execution time: {time.time() - start_time:.2f} seconds")
        
        if success:
            log("✅ ALL VALIDATIONS PASSED: Form is ready to submit!")
        else:
            log("❌ FORM VALIDATION FAILED: rspData is incomplete")
            
        return success

    except Exception as e:
        log(f"❌ Critical error: {str(e)}")
        return False