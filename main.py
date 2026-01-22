
import os
import json
import requests
import gspread
import pandas as pd
import io
from bs4 import BeautifulSoup

# --- 1. CONFIGURATION & SECRETS ---
# These names must match your GitHub Secrets exactly
USER = os.environ.get("SITE_EMAIL")
PASS = os.environ.get("SITE_PASSWORD")
COOKIE_VAL = os.environ.get("SESSION_COOKIE")

# --- 2. SETUP SESSION ---
session = requests.Session()
session.headers.update({
   "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"})

# --- 3. BYPASS 2FA (If using the Cookie Method) ---
# If you have a session cookie, we inject it here to pretend we are already logged in

if COOKIE_VAL:
    # We use 'PHPSESSID' because that is what your screenshot shows
    session.cookies.set('PHPSESSID', COOKIE_VAL, domain='app.easygo.com') 
    print("PHPSESSID cookie injected.")

# --- 4. LOGIN PROCESS (If not using cookies or if cookies expired) ---
login_url =  "https://app.easygoholidayhomes.com"
login_page = session.get(login_url)
soup = BeautifulSoup(login_page.text, 'html.parser')

Scrape the dynamic tokens
csrf_val = soup.find('input', {'name': 'csrftoken'})['value'] if soup.find('input', {'name': 'csrftoken'}) else ""
token_val = soup.find('input', {'name': 'token'})['value'] if soup.find('input', {'name': 'token'}) else ""

payload = {
    "user_name": USER,
    "user_password": PASS,
    "csrftoken": csrf_val,
    "token": token_val,
    "hashDevice": "" # Add if required by your site
}

# Perform Login
session.post(login_url, data=payload)

# --- 5. DOWNLOAD DATA ---
data_url = "https://app.easygoholidayhomes.com/index.php?estado%5B0%5D=CONFIRMADA&estado%5B1%5D=BAJOPETICION&estado%5B2%5D=PROPIETARIO&estado%5B3%5D=UNAVAILABLE&estado%5B4%5D=PAID&sortField=CREATION&sortOrder=DESC&module=Compromisos&action=ExportXlsPropietario&return_module=Compromisos&return_action=Ajax&avs=V0pwTWZhQkNwdG1VYS9Ca0RuNlhZMXRsZS9jcU1HUStRUEpGQ05lckJBQ3A2RlhxMVNWTDAvelFJSXV3NmNselMyN2Fjc0g3NkFNN1U0dlZ6UTJRdU5PTm1JeDR6cy9teWhsd1dEeXJwQ2lyMjFDUmF6SVVIclJTbVZaZzdadGRoZ3UxZ2hnVG9uZkFySURCcE54TzBOTmsvQVM2WG5oY3VEcmdYQWZYZEZwRkZQcWd3c1lrZytoK2Q3MnJnY1NOQlRkUXJtOHZWZEVZd0RERWlIZDN4UVN1TlppSWlLS29JMmdNZlJwOXpGZ1pVbGI3MkV5c0VqaWlLK2k5OWpVVzRXVlJjbWNuZHUwTXJLd0NXdGo4VXlyWUtrTU9LMVlJN08yUDNzbVIxeDNoVmliSUxjK2daZ0k5dFAxSXlCazZWczhQMmpqVVFybmw0NFRJN20wb1JRPT0%253D"
data_res = session.get(data_url)

# Validation: Ensure we actually got a CSV and not a login/error page
if "<html" in data_res.text.lower():
    print("Error: Received HTML instead of CSV.")
    exit(1)

df = pd.read_csv(io.StringIO(data_res.text))
print("Data successfully downloaded.")

# --- 6. SYNC TO GOOGLE SHEETS ---
# Load Google credentials from Secret
creds_dict = json.loads(os.environ["GOOGLE_SHEETS_CREDS"])
gc = gspread.service_account_from_dict(creds_dict)

# Open the sheet (Make sure you shared the sheet with the client_email!)
sh = gc.open("EasyGo Export")
worksheet = sh.get_worksheet(0)

# Clear old data and upload new data
worksheet.clear()
worksheet.update([df.columns.values.tolist()] + df.values.tolist())

print("Google Sheet updated successfully!")
