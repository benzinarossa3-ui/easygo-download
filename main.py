import os

# Securely grab credentials from GitHub Secrets
user = os.environ.get("SITE_EMAIL")
pw = os.environ.get("SITE_PASSWORD")




import json
import requests
import gspread
import pandas as pd
import io
from bs4 import BeautifulSoup

# 1. Setup Session & Login (as we discussed before)
session = requests.Session()
login_url = "https://app.easygoholidayhomes.com/index.php?module=Usuarios&action=Login&return_module=Home&return_action=index&avs=Q0Zqa1NCNWJ1WlNHUTdSeWhnY0lnR2phNWNFUnVhY3hSY2o0YnJYZnBWanBrdlB3MElqdEJyQlAwTkxnbUxCSG9HemZVTEUySit2eGlGcmNjRkR0QkFNZ3FIeGdUMXNtT093bjcvYkdCdkU9"
res = session.get(login_url)
soup = BeautifulSoup(res.text, 'html.parser')

payload = {
    "user_name": user,
    "user_password": pw,
    "csrftoken": soup.find('input', {'name': 'csrftoken'})['value'],
    "token": soup.find('input', {'name': 'token'})['value'],
}
session.post(login_url, data=payload)

# 2. Download Data
data_res = session.get("https://app.easygoholidayhomes.com/index.php?estado%5B0%5D=CONFIRMADA&estado%5B1%5D=BAJOPETICION&estado%5B2%5D=PROPIETARIO&estado%5B3%5D=UNAVAILABLE&estado%5B4%5D=PAID&sortField=CREATION&sortOrder=DESC&module=Compromisos&action=ExportXlsPropietario&return_module=Compromisos&return_action=Ajax&avs=V0pwTWZhQkNwdG1VYS9Ca0RuNlhZMXRsZS9jcU1HUStRUEpGQ05lckJBQ3A2RlhxMVNWTDAvelFJSXV3NmNselMyN2Fjc0g3NkFNN1U0dlZ6UTJRdU5PTm1JeDR6cy9teWhsd1dEeXJwQ2lyMjFDUmF6SVVIclJTbVZaZzdadGRoZ3UxZ2hnVG9uZkFySURCcE54TzBOTmsvQVM2WG5oY3VEcmdYQWZYZEZwRkZQcWd3c1lrZytoK2Q3MnJnY1NOQlRkUXJtOHZWZEVZd0RERWlIZDN4UVN1TlppSWlLS29JMmdNZlJwOXpGZ1pVbGI3MkV5c0VqaWlLK2k5OWpVVzRXVlJjbWNuZHUwTXJLd0NXdGo4VXlyWUtrTU9LMVlJN08yUDNzbVIxeDNoVmliSUxjK2daZ0k5dFAxSXlCazZWczhQMmpqVVFybmw0NFRJN20wb1JRPT0%253D")
df = pd.read_csv(io.StringIO(data_res.text))

# 3. Connect to Google Sheets using Secrets
# We get the JSON string from GitHub Environment Variables
creds_dict = json.loads(os.environ["GOOGLE_SHEETS_CREDS"])
gc = gspread.service_account_from_dict(creds_dict)

sh = gc.open("EasyGo Export")
worksheet = sh.get_worksheet(0)

# 4. Clear and Update
worksheet.clear()
worksheet.update([df.columns.values.tolist()] + df.values.tolist())
