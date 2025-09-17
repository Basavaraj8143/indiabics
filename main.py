from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time
import csv
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

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

for topic, pages in topics:
    total_pages = int(pages)
    topic_url = base_url + topic.lower().replace(' ', '-') + '/'
    driver.get(topic_url)
    time.sleep(2)

    # ✅ Extract category (breadcrumb/title)
    try:
        category_elem = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.pagehead h1"))
        )
        category_name = category_elem.text.strip()
    except:
        category_name = topic  # fallback if not found

    all_questions = []

    for page in range(1, total_pages + 1):
        print(f"\n=== Category: {category_name} | Topic: {topic} | Page {page} ===")

        try:
            # Wait for questions, options, answers
            questions = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "bix-td-qtxt")))
            options_blocks = driver.find_elements(By.CLASS_NAME, "bix-tbl-options")
            answer_divs = driver.find_elements(By.CSS_SELECTOR, "div.bix-div-answer")
            hidden_answers = driver.find_elements(By.CSS_SELECTOR, "input.jq-hdnakq")
        except TimeoutException:
            print(f"⚠️ Skipping Page {page} of {topic} (questions not found)")
            try:
                next_btn = driver.find_element(By.LINK_TEXT, "Next")
                driver.execute_script("arguments[0].click();", next_btn)
                time.sleep(2)
            except:
                print(f"⚠️ Could not find 'Next' button on page {page}")
            continue

        # Expand explanations
        for answer_div in answer_divs:
            try:
                driver.execute_script("arguments[0].classList.remove('collapse');", answer_div)
                driver.execute_script("arguments[0].classList.add('show');", answer_div)
            except:
                continue

        time.sleep(1)

        for i, (q, opts) in enumerate(zip(questions, options_blocks)):
            question_text = q.text.strip()

            # Extract options
            option_rows = opts.find_elements(By.CLASS_NAME, "bix-opt-row")
            option_texts = []
            for row in option_rows:
                try:
                    row.find_element(By.CLASS_NAME, "bix-td-option").text.strip()
                    value = row.find_element(By.CLASS_NAME, "bix-td-option-val").text.strip()
                    option_texts.append(value)
                except:
                    option_texts.append("N/A")

            while len(option_texts) < 4:
                option_texts.append("N/A")

            # Correct answer
            correct_answer = "N/A"
            if i < len(hidden_answers):
                correct_answer = hidden_answers[i].get_attribute("value").strip()

            # Explanation
            explanation_text = "No explanation available"
            if i < len(answer_divs):
                try:
                    explanation_elem = answer_divs[i].find_element(By.CSS_SELECTOR, ".bix-ans-description")
                    explanation_text = explanation_elem.text.strip() or explanation_text
                except:
                    pass

            print(f"Q{i+1}: {question_text}")
            print(f"Answer: {correct_answer}")
            print(f"Category: {category_name}")
            print(f"Explanation: {explanation_text}\n")

            all_questions.append([category_name, question_text] + option_texts[:4] + [correct_answer, explanation_text])

        # Next page
        if page < total_pages:
            try:
                next_btn = driver.find_element(By.LINK_TEXT, "Next")
                driver.execute_script("arguments[0].click();", next_btn)
                time.sleep(2)
            except:
                print(f"⚠️ Could not find 'Next' button on page {page}")
                break

    # Save CSV per topic
    file_name = topic.lower().replace(' ', '_') + '.csv'
    with open(os.path.join('output', file_name), 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Category", "Question", "Option A", "Option B", "Option C", "Option D", "Correct Answer", "Explanation"])
        writer.writerows(all_questions)

    print(f"✅ Saved {len(all_questions)} questions for topic: {topic}")

driver.quit()
print("Scraping completed!")
