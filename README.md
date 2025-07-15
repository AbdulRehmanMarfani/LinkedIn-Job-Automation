---

# LinkedIn Easy Apply Bot 🤖📩

A Python script that uses **Selenium WebDriver** to automate the **LinkedIn Easy Apply** process. The bot logs in securely using environment variables, navigates job listings, detects "Easy Apply" buttons, autofills phone numbers, and submits applications — skipping those with extra steps.

---

## Features 📋

* **Secure Login**: Uses `os.environ` to safely fetch LinkedIn email, password, and phone numbers.
* **Easy Apply Detection**: Finds and clicks the **Easy Apply** button if present.
* **Autofill Phone Number**: Inputs a phone number from a list of formats until accepted.
* **Single-Step Application Handling**: Submits applications only if no resume uploads or questionnaires are required.
* **Overlay & Modal Cleanup**: Dismisses popups, dialogs, and safety notices.
* **Randomized Behavior**: Mimics human browsing delays to avoid bot detection.
* **Failsafe Skipping**: Skips invalid or multi-step job applications without crashing.

---

## Libraries Used 🔌

* [`selenium`](https://pypi.org/project/selenium/)
* `os` (built-in)
* `time` (built-in)
* `random` (built-in)

---

## How It Works ⚙️

1. Opens LinkedIn's job search URL in Microsoft Edge.

2. Logs in using your email and password via environment variables.

3. Waits for manual CAPTCHA/puzzle solving.

4. Scrolls through all job cards on the page.

5. For each job:

   * Clicks the job card to load details.
   * Checks for an Easy Apply button.
   * Clicks the button if found.
   * Fills in the phone number (tries 2 formats).
   * If no extra steps are required:

     * Submits the application.
     * Closes confirmation modals.

6. Skips jobs with extra steps or invalid fields and continues gracefully.

---

## Setup 🛠️

### 1. Clone the Repo

```bash
git clone https://github.com/AbdulRehmanMarfani/linkedin-easy-apply-bot.git
cd linkedin-easy-apply-bot
```

### 2. Install Required Packages

```bash
pip install selenium
```

### 3. Install Microsoft Edge WebDriver

Download [Microsoft Edge WebDriver](https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/) and make sure it's added to your system PATH.

> ✅ Ensure the WebDriver version matches your installed Edge browser version.

### 4. Set Environment Variables

Add the following variables to your system environment or use a `.env` file:

```
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_secure_password
LINKEDIN_PHONE1=03272457411
LINKEDIN_PHONE2=3272457411
```

---

## Running the Script ▶️

```bash
python linkedin_easy_apply_bot.py
```

The bot will:

* Launch Microsoft Edge
* Log into LinkedIn
* Wait for you to solve any security puzzles
* Loop through job listings
* Apply to eligible ones using Easy Apply

---

## Sample Output 🖨️

```
Logged in and job cards loaded.
Clicked job card: Python Developer – XYZ Pvt Ltd
Button text: Easy Apply
Easy Apply clicked.
Tried phone: 03272457411, Value now: 03272457411
Application submitted.
Closed application confirmation modal.
```

---

## Security 🔐

This bot uses **environment variables** to store login credentials and phone numbers — no sensitive data is hardcoded.

> ⚠️ **Never commit credentials or `.env` files to public repositories.**

---

## Ideas for Extensions 🚀

* Add resume file upload support.
* Automatically handle multi-step applications with predefined answers.
* Integrate Telegram/email notifications after each apply.
* Add logging to CSV or Google Sheets.
* Rotate proxies or user agents for stealth mode.

---

## Legal Warning ⚠️

This bot **violates LinkedIn’s Terms of Service**. Use it **only for educational purposes** or on **test accounts**. Your account may get **restricted, flagged, or banned** if detected.

---
