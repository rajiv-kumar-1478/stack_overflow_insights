import requests
from bs4 import BeautifulSoup
import time
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed

# Headers to mimic a real browser
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive"
}

# Data storage
data_list = []
csv_filename = "pagedata.csv"

# Function to scrape Stack Overflow pages
def scrape_page(page_number):
    url = f"https://stackoverflow.com/questions?tab=newest&pagesize=50&page={page_number}"
    retries = 10  # Number of retries if rate limit is hit
    while retries > 0:
        try:
            print(f"🔍 Scraping Page {page_number}")
            response = requests.get(url, headers=headers, timeout=50)

            if response.status_code == 429:
                print(f"⚠️ Rate Limit Hit on Page {page_number}. Sleeping and Retrying...")
                time.sleep(10)
                retries -= 1
                continue  # Retry the request

            if response.status_code != 200:
                print(f"❌ Page {page_number} - Failed with Status {response.status_code}")
                return None

            soup = BeautifulSoup(response.text, "html.parser")
            questions = soup.select(".s-post-summary")

            page_data = []

            for q in questions:
                title_element = q.select_one(".s-post-summary--content-title a")
                question = title_element.text.strip() if title_element else "Unknown Title"

                tags = [tag.text.strip() for tag in q.select(".s-post-summary--meta-tags .post-tag")]

                date_element = q.select_one(".s-user-card--time .relativetime")
                date = date_element["title"][:10] if date_element and "title" in date_element.attrs else "Unknown Date"

                # Append formatted data
                page_data.append({
                    "Date": date,
                    "Tags": ", ".join(tags),  # Tags comma-separated
                    "Questions": question,  # Single question per row
                    "Page":page_number
                })

            time.sleep(2)  # Random delay to avoid bans
            return page_data

        except requests.exceptions.RequestException as e:
            print(f"❌ Page {page_number} - Error: {e}")
            return None

    print(f"❌ Skipping Page {page_number} after multiple failed attempts.")
    return None

# Using ThreadPoolExecutor for faster scraping
num_threads = 10  # Lower threads to avoid bans
pages_to_scrape = list(range(360, 5000))  # Define range of pages to scrape

with ThreadPoolExecutor(max_workers=num_threads) as executor:
    future_to_page = {executor.submit(scrape_page, page): page for page in pages_to_scrape}
    
    count = 0  # Counter to track number of pages processed

    for future in as_completed(future_to_page):
        result = future.result()
        if result:
            data_list.extend(result)
            count += 1

        # Save every 10 pages
        if count % 10 == 0:
            print(f"💾 Saving data to {csv_filename} after {count} pages")
            with open(csv_filename, mode="a", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=["Date","Tags", "Questions", "Page"])
                if file.tell() == 0:  # If file is empty, write header
                    writer.writeheader()
                writer.writerows(data_list)
            data_list.clear()  # Clear stored data to free memory

# Final Save (if any remaining data)
if data_list:
    print(f"💾 Final save to {csv_filename}")
    with open(csv_filename, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["Date","Tags", "Questions","Page"])
        if file.tell() == 0:  
            writer.writeheader()
        writer.writerows(data_list)

print(f"✅ Data saved to {csv_filename} successfully!")
