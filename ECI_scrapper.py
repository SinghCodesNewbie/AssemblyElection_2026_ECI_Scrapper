# pip install selenium pandas

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time

BASE_URL = "https://results.eci.gov.in/ResultAcGenMay2026/"

STATES = {
    "S03": "Assam",
    "S25": "West Bengal",
    "S22": "Tamil Nadu",
    "S11": "Kerala",
    "U07": "Puducherry"
}

OUTPUT_FILE = "ECI_Master_Results_2026.csv"


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
# PARTY NAME EXTRACTION (ROBUST)
# -------------------------------
def extract_party_name(driver):
    try:
        for tag in ["h2", "h3"]:
            elems = driver.find_elements(By.TAG_NAME, tag)
            if elems and elems[0].text.strip():
                return elems[0].text.strip()

        body = driver.find_element(By.TAG_NAME, "body").text
        for line in body.split("\n"):
            if "Party" in line or "PARTY" in line:
                return line.strip()

    except:
        pass

    return "Unknown"


# -------------------------------
# GET PARTY LINKS
# -------------------------------
def get_party_links(driver, state_code):
    url = BASE_URL + f"partywiseresult-{state_code}.htm"

    if not safe_get(driver, url):
        return []

    links = driver.find_elements(By.TAG_NAME, "a")

    party_links = []

    for link in links:
        href = link.get_attribute("href")

        if href and "partywisewinresult-" in href and state_code in href:
            party_links.append(href)

    return list(set(party_links))


# -------------------------------
# SCRAPE PARTY PAGE
# -------------------------------
def scrape_party_page(driver, url, state_name, state_code):
    if not safe_get(driver, url):
        return []

    data = []

    party_name = extract_party_name(driver)

    # party ID
    try:
        party_id = url.split("partywisewinresult-")[1].split(state_code)[0]
    except:
        party_id = ""

    rows = driver.find_elements(By.TAG_NAME, "tr")

    for row in rows:
        cols = row.find_elements(By.TAG_NAME, "td")

        if len(cols) >= 6:
            try:
                constituency = cols[1].text.strip()
                candidate = cols[2].text.strip()
                votes = cols[4].text.strip()
                margin = cols[5].text.strip()

                if not constituency or "Total" in constituency:
                    continue

                data.append({
                    "State": state_name,
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
# MAIN RUNNER
# -------------------------------
def run():
    driver = setup_driver()

    all_data = []
    visited = set()

    print("🚀 Starting MASTER ECI Scraper...\n")

    for state_code, state_name in STATES.items():

        print(f"📊 Scraping {state_name}")

        party_links = get_party_links(driver, state_code)

        print(f"➡️ {len(party_links)} party links found")

        for link in party_links:

            if link in visited:
                continue

            visited.add(link)

            try:
                data = scrape_party_page(driver, link, state_name, state_code)

                if data:
                    all_data.extend(data)
                    print(f"✅ {len(data)} rows scraped")
                else:
                    print(f"⚠️ Empty: {link}")

            except:
                print(f"❌ Failed: {link}")

    driver.quit()

    df = pd.DataFrame(all_data)
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"\n✅ DONE — Master file saved as: {OUTPUT_FILE}")


# -------------------------------
# RUN
# -------------------------------
if __name__ == "__main__":
    run()
