from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import os
import time
import csv
from datetime import datetime

# Create output folder
os.makedirs('output', exist_ok=True)

# Load topics with page counts from topics.txt
with open('topics.txt', 'r') as file:
    topics = [line.strip().split(',') for line in file.readlines()]

# Configure Chrome (headless + suppress logs)
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--log-level=3")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

# Initialize Selenium
driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 10)
base_url = "https://www.indiabix.com/aptitude/"

# CSV header (match DB schema)
headers = [
    "id", "category_id", "question_text",
    "option_a", "option_b", "option_c", "option_d",
    "correct_answer", "explanation",
    "difficulty", "marks", "is_active",
    "created_by", "created_at"
]

for topic, pages in topics:
    total_pages = int(pages)
    topic_url = base_url + topic.lower().replace(' ', '-') + '/'
    driver.get(topic_url)
    time.sleep(2)
    
    rows = []
    q_id = 1  # reset for each topic

    for page in range(1, total_pages + 1):
        print(f"\n=== Topic: {topic} | Page {page} ===")
        
        try:
            questions = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "bix-td-qtxt")))
            options_blocks = driver.find_elements(By.CLASS_NAME, "bix-tbl-options")
            answers = driver.find_elements(By.CSS_SELECTOR, "input.jq-hdnakq")  # hidden inputs for correct answer
            explanations = driver.find_elements(By.CSS_SELECTOR, "div.bix-ans-description")
        except TimeoutException:
            print(f"⚠️ Skipping Page {page} of {topic}")
            continue

        for i, (q, opts, ans) in enumerate(zip(questions, options_blocks, answers), 1):
            question_text = q.text.strip()
            print(f"Q{i}: {question_text}")

            # Extract options
            option_rows = opts.find_elements(By.CLASS_NAME, "bix-opt-row")
            option_texts = ["", "", "", ""]
            for row in option_rows:
                try:
                    label = row.find_element(By.CLASS_NAME, "bix-td-option").text.strip().replace(".", "")
                    value = row.find_element(By.CLASS_NAME, "bix-td-option-val").text.strip()
                    if label in ["A", "B", "C", "D"]:
                        option_texts[ord(label) - ord("A")] = value
                except:
                    continue

            # Correct Answer
            correct_answer = ans.get_attribute("value")

            # Explanation
            explanation = "No explanation"
            if i-1 < len(explanations):
                exp_text = explanations[i-1].text.strip()
                if exp_text:
                    explanation = exp_text

            # Defaults
            difficulty = "Medium"
            marks = 1
            is_active = 1
            created_by = "system"
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Build row
            row = [
                q_id, topic, question_text,
                option_texts[0], option_texts[1], option_texts[2], option_texts[3],
                correct_answer, explanation,
                difficulty, marks, is_active,
                created_by, created_at
            ]
            rows.append(row)
            q_id += 1

        # Next page
        if page < total_pages:
            try:
                next_btn = driver.find_element(By.LINK_TEXT, "Next")
                driver.execute_script("arguments[0].click();", next_btn)
                time.sleep(2)
            except:
                break

    # Save CSV
    file_name = topic.lower().replace(' ', '_') + '.csv'
    with open(os.path.join('output', file_name), 'w', encoding='utf-8', newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    
    print(f"✅ Saved {len(rows)} questions for topic: {topic} → {file_name}")

driver.quit()
print("🎉 Scraping completed!")
