import sys
import time
import csv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

if len(sys.argv) < 2:
    print("Error: Target URL argument missing.")
    sys.exit(1)

target_url = sys.argv[1]

# Explicit identification for logging
if "analyst-reference-guide" in target_url:
    app_id = "guide"
elif "professional-portfolio" in target_url or "portfolio" in target_url:
    app_id = "portfolio"
else:
    app_id = "app"

options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def check_app(url):
    start_time = time.time()
    
    for attempt in range(3):
        try:
            print(f"Attempt {attempt + 1} for [{app_id}]: {url}")
            driver.get(url)
            
            # Allow time for initial network connection
            time.sleep(6)
            
            # --- 1. HANDLE WAKE-UP BUTTON IF ASLEEP ---
            try:
                wake_buttons = driver.find_elements(
                    By.XPATH, 
                    "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'back up') "
                    "or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'wake')]"
                )
                if wake_buttons:
                    print(f"⚠️ [{app_id}] is sleeping. Clicking wake-up button...")
                    wake_buttons[0].click()
                    time.sleep(15)  # Allow container cold-start spin-up
            except Exception:
                pass
            
            # --- 2. VERIFY CORE APP RENDER ---
            # Wait for either the guide title, the portfolio welcome title, or an h1/h2 element
            WebDriverWait(driver, 35).until(
                EC.presence_of_element_located((
                    By.XPATH, 
                    "//*[contains(text(), 'Knowledge Repository') or contains(text(), 'Analyst Hub') or contains(text(), 'Welcome') or self::h1 or self::h2]"
                ))
            )
            
            load_time = round(time.time() - start_time, 2)
            return load_time, "Success"
            
        except Exception as e:
            print(f"Attempt {attempt + 1} for [{app_id}] failed. Details: {str(e)[:120]}")
            if attempt == 2:
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
                error_filename = f"error_{app_id}_{timestamp}.png"
                try:
                    driver.save_screenshot(error_filename)
                    print(f"Screenshot saved: {error_filename}")
                except Exception:
                    pass
    
    return 0, "Failed"

try:
    duration, status = check_app(target_url)
    
    with open('app_performance_log.csv', mode='a', newline='') as f:
        csv.writer(f).writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), app_id, duration, status])
        
    if status == "Success":
        print(f"✅ [{app_id}] is LIVE ({duration}s)")
    else:
        print(f"❌ [{app_id}] FAILED - Check error screenshot in repo if generated.")
        sys.exit(1)
finally:
    driver.quit()
