# pip install selenium pandas

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time

BASE_URL = "https://results.eci.gov.in/ResultAcGenMay2026/"
STATE_CODE = "U07"
STATE_NAME = "Puducherry"

SAVE_FILE = "Puducherry Final sheet.csv"


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
# SAFE LOAD
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
# ROBUST PARTY NAME EXTRACTION
# -------------------------------
def extract_party_name(driver):
    try:
        # h2
        h2 = driver.find_elements(By.TAG_NAME, "h2")
        if h2 and h2[0].text.strip():
            return h2[0].text.strip()

        # h3
        h3 = driver.find_elements(By.TAG_NAME, "h3")
        if h3 and h3[0].text.strip():
            return h3[0].text.strip()

        # fallback
        body = driver.find_element(By.TAG_NAME, "body").text

        for line in body.split("\n"):
            if "Party" in line or "PARTY" in line:
                return line.strip()

    except:
        pass

    return "Unknown"


# -------------------------------
# SCRAPE PARTY PAGE
# -------------------------------
def scrape_party_page(driver, url):
    if not safe_get(driver, url):
        return []

    data = []

    party_name = extract_party_name(driver)

    # party ID
    try:
        party_id = url.split("partywisewinresult-")[1].split("U")[0]
    except:
        party_id = ""

    rows = driver.find_elements(By.TAG_NAME, "tr")

    for row in rows:
        cols = row.find_elements(By.TAG_NAME, "td")

        # U07 sometimes has 5 or 6 cols → handle both
        if len(cols) >= 5:
            try:
                constituency = cols[1].text.strip()
                candidate = cols[2].text.strip()
                votes = cols[3].text.strip()
                margin = cols[4].text.strip()

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

            except:
                continue

    return data


# -------------------------------
# MAIN
# -------------------------------
def run():
    driver = setup_driver()

    all_data = []
    visited = set()

    print("🚀 Scraping Puducherry...")

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
