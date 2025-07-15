import os
import time
import random
import logging
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException

# Logging to file and console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("linkedin_job_apply.log"),
        logging.StreamHandler()
    ]
)

CONFIG = {
    "url": os.environ.get("LINKEDIN_JOB_URL", "https://www.linkedin.com/jobs/search/?currentJobId=4266578007&distance=100&f_AL=true&geoId=118918281&keywords=python%20developer&origin=JOB_SEARCH_PAGE_JOB_FILTER"),
    "user_agent": os.environ.get("LINKEDIN_USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
    "sleep_short": float(os.environ.get("LINKEDIN_SLEEP_SHORT", 0.8)),
    "sleep_long": float(os.environ.get("LINKEDIN_SLEEP_LONG", 1.5)),
    "headless": os.environ.get("HEADLESS", "0") == "1",
    "job_blacklist_keywords": os.environ.get("JOB_BLACKLIST", "senior,lead,manager").split(","),
}

email = os.environ.get("LINKEDIN_EMAIL")
password = os.environ.get("LINKEDIN_PASSWORD")
phone_numbers = [os.environ.get("LINKEDIN_PHONE1"), os.environ.get("LINKEDIN_PHONE2")]

def mask_sensitive(value):
    """Mask all but last 2 characters of sensitive info."""
    if not value:
        return ""
    return "*" * (len(value) - 2) + value[-2:]

def close_modals(driver):
    """Close any open modal dialogs."""
    try:
        close_buttons = driver.find_elements(By.CLASS_NAME, "artdeco-modal__dismiss")
        for btn in close_buttons:
            btn.click()
            time.sleep(random.uniform(CONFIG["sleep_short"], CONFIG["sleep_long"]))
    except Exception as e:
        logging.warning("Could not close modal: %s", e)

def handle_phone_input(driver, phone_input, phone_numbers):
    """Try all phone numbers and return True if one is accepted."""
    for number in phone_numbers:
        if not number:
            continue
        try:
            phone_input.clear()
            phone_input.click()
            driver.execute_script("""
                arguments[0].value = arguments[1];
                arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
            """, phone_input, number)
            time.sleep(random.uniform(0.6, 1.2))
            logging.info("Tried phone: %s", mask_sensitive(number))
            error_elements = driver.find_elements(By.XPATH, "//span[contains(text(), 'Enter a valid phone number')]")
            if not error_elements:
                return True
        except Exception as e:
            logging.warning("Could not fill phone number: %s", e)
    return False

def is_captcha_present(driver):
    """Detect if a captcha is present."""
    try:
        captcha = driver.find_elements(By.XPATH, "//iframe[contains(@src, 'captcha')]")
        return bool(captcha)
    except Exception:
        return False

def job_is_blacklisted(job_text):
    """Return True if job contains blacklisted keywords."""
    for keyword in CONFIG["job_blacklist_keywords"]:
        if keyword.strip().lower() in job_text.lower():
            return True
    return False

def retry(action, retries=3, delay=1):
    """Retry a function up to `retries` times."""
    for attempt in range(retries):
        try:
            return action()
        except Exception as e:
            logging.warning("Retry %d/%d failed: %s", attempt+1, retries, e)
            time.sleep(delay)
    raise

def login(driver, email, password, url):
    """Login to LinkedIn."""
    driver.get(url)
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@id='base-contextual-sign-in-modal']/div/section/div/div/div/div[2]/button"))
        ).click()
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='base-sign-in-modal_session_key']"))
        )
        email_input.send_keys(email)
        password_input = driver.find_element(By.XPATH, "//*[@id='base-sign-in-modal_session_password']")
        password_input.send_keys(password)
        password_input.send_keys(Keys.ENTER)
    except NoSuchElementException as e:
        logging.error("Login element not found: %s", e)
        driver.quit()
        raise
    except ElementClickInterceptedException as e:
        logging.error("Could not click login element: %s", e)
        driver.quit()
        raise

    if is_captcha_present(driver):
        logging.warning("Captcha detected! Please solve it manually.")
        input("Solve the LinkedIn captcha, then press Enter to continue...")

    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "job-card-container"))
        )
        logging.info("Logged in and job cards loaded.")
    except TimeoutException as e:
        logging.error("Login or job card load timed out: %s", e)
        driver.quit()
        raise
    except Exception as e:
        logging.error("Login or job card load failed: %s", e)
        driver.quit()
        raise

def apply_to_jobs(driver, phone_numbers):
    """Apply to jobs using Easy Apply."""
    jobs = driver.find_elements(By.CLASS_NAME, "job-card-container")
    logging.info("Found %d jobs.", len(jobs))
    for i in range(len(jobs)):
        try:
            jobs = driver.find_elements(By.CLASS_NAME, "job-card-container")
            job = jobs[i]
            job_text = job.text
            if job_is_blacklisted(job_text):
                logging.info("Skipped blacklisted job: %s", job_text.split("\n")[0])
                continue

            try:
                close_modals(driver)
            except Exception:
                pass

            driver.execute_script("arguments[0].scrollIntoView();", job)
            time.sleep(random.uniform(2, 4))
            try:
                ActionChains(driver).move_to_element(job).click().perform()
            except Exception:
                driver.execute_script("arguments[0].click();", job)
            logging.info("Clicked job card: %s", job.text.split("\n")[0])

            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'jobs-details')]"))
                )
                logging.info("Job details loaded.")
            except Exception as e:
                logging.warning("Job details did not load, skipping job: %s", e)
                continue

            try:
                easy_apply_buttons = driver.find_elements(By.XPATH, "//button[contains(@class, 'jobs-apply-button')]")
                found = False
                for btn in easy_apply_buttons:
                    logging.info("Button text: %s", btn.text)
                    if "Easy Apply" in btn.text:
                        driver.execute_script("arguments[0].scrollIntoView();", btn)
                        time.sleep(random.uniform(0.4, 1.0))
                        driver.execute_script("arguments[0].click();", btn)
                        logging.info("Easy Apply clicked.")
                        found = True
                        break
                if not found:
                    logging.warning("No Easy Apply button for this job or not clickable.")
                    continue
            except Exception as e:
                logging.warning("No Easy Apply button for this job or not clickable: %s", e)
                continue

            try:
                phone_inputs = driver.find_elements(By.XPATH, "//input[@name='phoneNumber']")
                submit_buttons = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Submit application')]")
                next_buttons = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Continue to next step')]")
                review_buttons = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Review your application')]")

                if submit_buttons and not next_buttons and not review_buttons:
                    if phone_inputs:
                        phone_input = phone_inputs[0]
                        phone_filled = handle_phone_input(driver, phone_input, phone_numbers)
                        if not phone_filled:
                            logging.warning("All phone formats failed, skipping application.")
                            close_modals(driver)
                            continue
                    submit_button = submit_buttons[0]
                    driver.execute_script("arguments[0].click();", submit_button)
                    time.sleep(random.uniform(CONFIG["sleep_short"], CONFIG["sleep_long"]))
                    error_elements = driver.find_elements(By.XPATH, "//span[contains(text(), 'Enter a valid phone number')]")
                    if error_elements:
                        logging.warning("Phone number validation error, could not submit application.")
                        close_modals(driver)
                        continue
                    save_dialog = driver.find_elements(By.XPATH, "//div[contains(text(), 'Save this application?')]")
                    if save_dialog:
                        discard_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Discard')]")
                        for btn in discard_btns:
                            if btn.is_displayed():
                                btn.click()
                                logging.info("Application was not submitted (Save dialog appeared, discarded).")
                                break
                        continue
                    logging.info("Application submitted.")
                    try:
                        close_btns = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Dismiss') or contains(@aria-label, 'Close')]")
                        for btn in close_btns:
                            if btn.is_displayed():
                                btn.click()
                                logging.info("Closed application confirmation modal.")
                                time.sleep(1)
                                break
                    except Exception as e:
                        logging.warning("Could not close confirmation modal: %s", e)
                else:
                    logging.info("Extra requirements detected, skipping job.")
                    close_modals(driver)
                    try:
                        discard_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Discard')]")
                        for btn in discard_btns:
                            if btn.is_displayed():
                                btn.click()
                                logging.info("Clicked Discard on save dialog.")
                                break
                    except Exception:
                        pass
            except Exception as e:
                logging.error("Error during application: %s", e)

            try:
                continue_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Continue applying')]")
                for btn in continue_btns:
                    if btn.is_displayed():
                        btn.click()
                        logging.info("Clicked Continue applying on safety reminder.")
                        time.sleep(1)
                        break
            except Exception:
                pass

        except ConnectionResetError as cre:
            logging.warning("Connection reset by LinkedIn, retrying after delay...")
            time.sleep(random.uniform(10, 20))
            continue
        except Exception as e:
            logging.error("Error processing job: %s", type(e).__name__, e)

    # Notification on completion
    logging.info("All jobs processed. Script finished.")

if __name__ == "__main__":
    edge_options = webdriver.EdgeOptions()
    edge_options.add_experimental_option("detach", True)
    edge_options.add_argument(f"user-agent={CONFIG['user_agent']}")
    if CONFIG["headless"]:
        edge_options.add_argument("--headless")
    driver = webdriver.Edge(options=edge_options)

    if not email or not password:
        logging.error("Email or password not set in environment variables.")
        sys.exit(1)

    try:
        login(driver, email, password, CONFIG["url"])
        apply_to_jobs(driver, phone_numbers)
    finally:
        driver.quit()
        logging.info("Web driver closed.")
        logging.info("Script execution completed.")
        sys.exit(0)
