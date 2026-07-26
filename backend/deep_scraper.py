from playwright.sync_api import sync_playwright
import time

def scrape_berkeley_department(department="COMPSCI"):
    print(f"Starting pagination scraper for {department}...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        page_number = 0
        all_class_links = []
        
        while True:
            # YOUR URL STRUCTURE IN ACTION:
            search_url = f"https://classes.berkeley.edu/search/class?search={department}&f%5B0%5D=term%3A8588&page={page_number}"
            print(f"\nLoading {department} Page {page_number}...")
            page.goto(search_url)
            
            try:
                # Wait for the specific row container you found
                page.wait_for_selector(".st--section-name-wraper", timeout=15000)
            except Exception:
                # If it times out, we assume we hit a blank page and reached the end of the catalog
                print(f"No classes found on page {page_number}. Ending pagination.")
                break
                
            # Grab all the links inside that specific container
            # The space between the class name and the 'a' means "find all <a> tags INSIDE this class"
            # Grab all the row containers on the page
            row_containers = page.locator(".st--section-name-wraper").all()
            page_links = []
            
            for container in row_containers:
                # Target ONLY the first link inside this specific row
                first_link = container.locator("a").first
                href = first_link.get_attribute("href")
                
                if href:
                    # Safety check: if the link is an external website, skip it
                    if href.startswith("http"):
                        continue
                    # Otherwise, it is a relative link (like /content/2026-fall...) so we build the full URL
                    page_links.append(f"https://classes.berkeley.edu{href}")
                    
            print(f"Found {len(page_links)} classes on this page.")
            all_class_links.extend(page_links)
            
            # Move to the next page!
            page_number += 1
            time.sleep(2) # Pause briefly so we don't spam the Berkeley servers
            
        print(f"\n--- SUCCESS ---")
        print(f"\nCollected {len(all_class_links)} class links. Starting deep scrape...")
        
        detailed_courses = []
        for link in all_class_links:
            print(f"Scraping {link}...")
            page.goto(link)
            
            try:
                # Wait for the main content to load
                page.wait_for_selector("body", timeout=10000)
                
                # Get all the raw text on the page
                page_text = page.locator("body").inner_text()
                
                # Split the text into individual lines and remove any blank lines
                lines = [line.strip() for line in page_text.split('\n') if line.strip()]
                
                title = page.locator("h1").first.inner_text() if page.locator("h1").count() > 0 else "Unknown Title"
                
                # Initialize default values
                open_seats = "0"
                waitlist = "0"
                enrolled = "0"
                capacity = "0"
                prereqs = "None"
                reserved_rules = "None"
                
                # Loop through the lines to find our specific keywords
                for i, line in enumerate(lines):
                    # 1. Seat Counts
                    if line.startswith("Total Open Seats:"):
                        open_seats = line.split(":")[-1].strip()
                    elif line.startswith("Enrolled:"):
                        enrolled = line.split(":")[-1].strip()
                    elif line.startswith("Waitlisted:"):
                        waitlist = line.split(":")[-1].strip()
                    elif line.startswith("Capacity:"):
                        capacity = line.split(":")[-1].strip()
                        
                    # 2. Requisites / Prerequisites
                    elif line == "Requisites":
                        # The actual requisite rules are printed on the very next line
                        if i + 1 < len(lines):
                            prereqs = lines[i+1]
                            
                    # 3. Reserved Seats
                    # 3. Reserved Seats (Multi-line fix)
                    elif line == "Open Reserved Seats:":
                        reserved_list = []
                        j = i + 1
                        # Keep grabbing lines until we hit the next known header
                        while j < len(lines) and lines[j] not in ["Textbooks & Materials", "Also offered as:", "Hours & Workload", "Early Drop Deadline"]:
                            reserved_list.append(lines[j])
                            j += 1
                        
                        # Join them together with a separator so it stays clean in your database
                        reserved_rules = " | ".join(reserved_list)

                # Store the extracted data
                detailed_courses.append({
                    "url": link,
                    "title": title,
                    "open_seats": open_seats,
                    "enrolled": enrolled,
                    "waitlisted": waitlist,
                    "capacity": capacity,
                    "prerequisites": prereqs,
                    "reserved_rules": reserved_rules
                })
                
                print(f"  -> Seats: {open_seats}/{capacity} | Waitlist: {waitlist} | Reserved: {reserved_rules}")
                
            except Exception as e:
                print(f"Timed out or error on {link}: {e}")
                continue
                
            time.sleep(2) # Pause briefly so we don't spam the Berkeley servers
        
        # NOTE: At this point, you would loop through `all_class_links` 
        # and visit each one to get the seat counts, just like the previous script.
        
        browser.close()
        return all_class_links

if __name__ == "__main__":
    links = scrape_berkeley_department("COMPSCI")