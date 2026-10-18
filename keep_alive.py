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
    sys.exit(0)

target_url = sys.argv[1]

# App identifier
if "analyst-reference-guide" in target_url:
    app_id = "guide"
elif "professional-portfolio" in target_url or "portfolio" in target_url:
    app_id = "portfolio"
else:
    app_id = "app"

# Configure headless Chrome for GitHub Actions runners
options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--disable-extensions")
options.add_argument("--window-size=1920,1080")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

driver = None
status = "Failed"
load_time = 0.0

try:
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    start_time = time.time()
    print(f"Pinging [{app_id}]: {target_url}")
    
    driver.get(target_url)
    time.sleep(8)

    # 1. Wake up if sleeping
    try:
        wake_buttons = driver.find_elements(
            By.XPATH, 
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'back up') "
            "or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'wake')]"
        )
        if wake_buttons:
            print(f"⚠️ [{app_id}] is sleeping. Clicking wake-up button...")
            wake_buttons[0].click()
            time.sleep(15)
    except Exception:
        pass

    # 2. Wait for Streamlit root container or primary content
    WebDriverWait(driver, 35).until(
        EC.presence_of_element_located((
            By.CSS_SELECTOR, 
            "#root, .stApp, [data-testid='stAppViewContainer'], header, section.main"
        ))
    )

    load_time = round(time.time() - start_time, 2)
    status = "Success"
    print(f"✅ [{app_id}] is LIVE ({load_time}s)")

except Exception as e:
    print(f"⚠️ [{app_id}] encounter error/timeout: {str(e)[:120]}")
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        error_filename = f"error_{app_id}_{timestamp}.png"
        driver.save_screenshot(error_filename)
        print(f"Screenshot captured: {error_filename}")
    except Exception:
        pass

finally:
    if driver:
        driver.quit()

    # Append metrics to CSV for the System Health chart
    try:
        with open('app_performance_log.csv', mode='a', newline='') as f:
            csv.writer(f).writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), app_id, load_time, status])
        print(f"Metrics logged to app_performance_log.csv: {status} ({load_time}s)")
    except Exception as err:
        print(f"Failed to write CSV: {err}")

    # Exit cleanly so GitHub Actions does not fail the runner
    sys.exit(0)
