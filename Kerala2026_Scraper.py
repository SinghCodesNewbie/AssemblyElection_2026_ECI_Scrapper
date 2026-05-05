# pip install selenium pandas

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time
import os

BASE_URL = "https://results.eci.gov.in/ResultAcGenMay2026/"
STATE_CODE = "S11"   # as per your mapping
STATE_NAME = "Kerala"

SAVE_FILE = "Kerala Final sheet.csv"


# -------------------------------
# DRIVER SETUP
# -------------------------------
def setup_driver():
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--user-agent=Mozilla/5.0")

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)

    return driver


# -------------------------------
# SAFE PAGE LOAD
# -------------------------------
def safe_get(driver, url, retries=3):
    for i in range(retries):
        try:
            driver.get(url)
            time.sleep(2)

            if "Constituency" in driver.page_source:
                return True

        except:
            pass

        print(f"Retry {i+1}: {url}")
        time.sleep(2)

    return False


# -------------------------------
# GET PARTY LINKS
# -------------------------------
def get_party_links(driver):
    url = BASE_URL + f"partywiseresult-{STATE_CODE}.htm"

    if not safe_get(driver, url):
        return []

    links = driver.find_elements(By.TAG_NAME, "a")

    party_links = []

    for link in links:
        href = link.get_attribute("href")

        if href and "partywisewinresult-" in href and href.endswith(f"{STATE_CODE}.htm"):
            party_links.append(href)

    return list(set(party_links))


# -------------------------------
# SCRAPE PARTY PAGE
# -------------------------------
def scrape_party_page(driver, url):
    if not safe_get(driver, url):
        return []

    data = []

    # Party name
    party_name = "Unknown"
    try:
        heading = driver.find_element(By.TAG_NAME, "h2")
        party_name = heading.text.strip()
    except:
        pass

    # Party ID
    try:
        party_id = url.split("partywisewinresult-")[1].split("S")[0]
    except:
        party_id = ""

    rows = driver.find_elements(By.TAG_NAME, "tr")

    for row in rows:
        cols = row.find_elements(By.TAG_NAME, "td")

        if len(cols) >= 6:
            constituency = cols[1].text.strip()
            candidate = cols[2].text.strip()
            votes = cols[4].text.strip()
            margin = cols[5].text.strip()

            if not constituency or "Total" in constituency:
                continue

            data.append({
                "State": STATE_NAME,
                "Constituency": constituency,
                "Candidate": candidate,
                "Party": party_name,
                "Party_ID": party_id,
                "Votes": votes,
                "Margin": margin
            })

    return data


# -------------------------------
# MAIN RUN
# -------------------------------
def run():
    driver = setup_driver()

    all_data = []
    visited = set()

    print("🚀 Scraping Kerala...")

    party_links = get_party_links(driver)
    print(f"➡️ {len(party_links)} party links found")

    for link in party_links:

        if link in visited:
            continue

        visited.add(link)

        data = scrape_party_page(driver, link)

        if data:
            all_data.extend(data)
            print(f"✅ {len(data)} rows scraped")
        else:
            print(f"⚠️ Skipped: {link}")

    driver.quit()

    df = pd.DataFrame(all_data)
    df.to_csv(SAVE_FILE, index=False)

    print(f"\n✅ DONE — Saved as: {SAVE_FILE}")


# -------------------------------
# RUN
# -------------------------------
if __name__ == "__main__":
    run()
