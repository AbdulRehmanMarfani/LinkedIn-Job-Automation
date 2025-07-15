import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import random

url = "https://www.linkedin.com/jobs/search/?currentJobId=4266578007&distance=100&f_AL=true&geoId=118918281&keywords=python%20developer&origin=JOB_SEARCH_PAGE_JOB_FILTER"
email = os.environ.get("LINKEDIN_EMAIL")
password = os.environ.get("LINKEDIN_PASSWORD")
phone_numbers = [os.environ.get("LINKEDIN_PHONE1"), os.environ.get("LINKEDIN_PHONE2")]

edge_options = webdriver.EdgeOptions()
edge_options.add_experimental_option("detach", True)
edge_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
driver = webdriver.Edge(options=edge_options)

driver.get(url)
driver.implicitly_wait(10)

driver.find_element(By.XPATH, "//*[@id='base-contextual-sign-in-modal']/div/section/div/div/div/div[2]/button").click()
email_input = driver.find_element(By.XPATH, "//*[@id='base-sign-in-modal_session_key']")
email_input.send_keys(email)
password_input = driver.find_element(By.XPATH, "//*[@id='base-sign-in-modal_session_password']")
password_input.send_keys(password)
password_input.send_keys(Keys.ENTER)

input("Solve the LinkedIn puzzle manually, then press Enter to continue...")

try:
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CLASS_NAME, "job-card-container"))
    )
    print("Logged in and job cards loaded.")
except Exception as e:
    print("Login or job card load failed:", e)
    driver.quit()
    exit()

jobs = driver.find_elements(By.CLASS_NAME, "job-card-container")
print(jobs)

for i in range(len(jobs)):
    try:
        jobs = driver.find_elements(By.CLASS_NAME, "job-card-container")
        job = jobs[i]

        try:
            close_buttons = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Dismiss')]")
            for btn in close_buttons:
                btn.click()
                time.sleep(0.5)
        except Exception:
            pass

        driver.execute_script("arguments[0].scrollIntoView();", job)
        time.sleep(random.uniform(2, 4))
        try:
            ActionChains(driver).move_to_element(job).click().perform()
        except Exception:
            driver.execute_script("arguments[0].click();", job)
        print("Clicked job card:", job.text)

        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'jobs-details')]"))
            )
            print("Job details loaded.")
        except Exception as e:
            print("Job details did not load, skipping job:", e)
            continue

        try:
            easy_apply_buttons = driver.find_elements(By.XPATH, "//button[contains(@class, 'jobs-apply-button')]")
            found = False
            for btn in easy_apply_buttons:
                print("Button text:", btn.text)
                if "Easy Apply" in btn.text:
                    driver.execute_script("arguments[0].scrollIntoView();", btn)
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", btn)
                    print("Easy Apply clicked.")
                    found = True
                    break
            if not found:
                print("No Easy Apply button for this job or not clickable.")
                continue
        except Exception as e:
            print("No Easy Apply button for this job or not clickable.", e)
            continue

        try:
            phone_inputs = driver.find_elements(By.XPATH, "//input[@name='phoneNumber']")
            submit_buttons = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Submit application')]")
            next_buttons = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Continue to next step')]")
            review_buttons = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Review your application')]")

            if submit_buttons and not next_buttons and not review_buttons:
                if phone_inputs:
                    phone_input = phone_inputs[0]
                    phone_filled = False
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
                            time.sleep(0.7)
                            print(f"Tried phone: {number}, Value now: {phone_input.get_attribute('value')}")
                            error_elements = driver.find_elements(By.XPATH, "//span[contains(text(), 'Enter a valid phone number')]")
                            if not error_elements:
                                phone_filled = True
                                break
                        except Exception as e:
                            print("Could not fill phone number:", e)
                    if not phone_filled:
                        print("All phone formats failed, skipping application.")
                        close_buttons = driver.find_elements(By.CLASS_NAME, "artdeco-modal__dismiss")
                        for btn in close_buttons:
                            btn.click()
                        time.sleep(1)
                        continue
                submit_button = submit_buttons[0]
                driver.execute_script("arguments[0].click();", submit_button)
                time.sleep(1)
                error_elements = driver.find_elements(By.XPATH, "//span[contains(text(), 'Enter a valid phone number')]")
                if error_elements:
                    print("Phone number validation error, could not submit application.")
                    close_buttons = driver.find_elements(By.CLASS_NAME, "artdeco-modal__dismiss")
                    for btn in close_buttons:
                        btn.click()
                    time.sleep(1)
                    continue
                save_dialog = driver.find_elements(By.XPATH, "//div[contains(text(), 'Save this application?')]")
                if save_dialog:
                    discard_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Discard')]")
                    for btn in discard_btns:
                        if btn.is_displayed():
                            btn.click()
                            print("Application was not submitted (Save dialog appeared, discarded).")
                            break
                    continue
                print("Application submitted.")
                try:
                    close_btns = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Dismiss') or contains(@aria-label, 'Close')]")
                    for btn in close_btns:
                        if btn.is_displayed():
                            btn.click()
                            print("Closed application confirmation modal.")
                            time.sleep(1)
                            break
                except Exception as e:
                    print("Could not close confirmation modal:", e)
            else:
                print("Extra requirements detected, skipping job.")
                close_buttons = driver.find_elements(By.CLASS_NAME, "artdeco-modal__dismiss")
                for btn in close_buttons:
                    btn.click()
                time.sleep(1)
                try:
                    discard_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Discard')]")
                    for btn in discard_btns:
                        if btn.is_displayed():
                            btn.click()
                            print("Clicked Discard on save dialog.")
                            break
                except Exception:
                    pass
        except Exception as e:
            print("Error during application:", e)

        try:
            continue_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Continue applying')]")
            for btn in continue_btns:
                if btn.is_displayed():
                    btn.click()
                    print("Clicked Continue applying on safety reminder.")
                    time.sleep(1)
                    break
        except Exception:
            pass

    except ConnectionResetError as cre:
        print("Connection reset by LinkedIn, retrying after delay...")
        time.sleep(random.uniform(10, 20))
        continue
    except Exception as e:
        print("Error processing job:", type(e).__name__, e)

driver.quit()
