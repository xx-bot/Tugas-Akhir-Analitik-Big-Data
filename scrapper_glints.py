import csv
import time
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from curl_cffi import requests
from bs4 import BeautifulSoup
import os

class GlintsScraper:
    def __init__(self, cookie_dict):
        self.url = 'https://glints.com/api/v2-alc/graphql'
        self.session = requests.Session()
        
        cookie_string = "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])
        
        self.headers = {
            "accept": "*/*",
            "content-type": "application/json",
            "origin": "https://glints.com",
            'referer': 'https://glints.com/id/opportunities/jobs/explore',
            "x-glints-country-code": "ID",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "cookie": cookie_string
        }

    def fetch_job_list(self, page, category_id):
        json_data = {
            'operationName': 'searchJobsV3',
            'variables': {
                'data': {
                    'CountryCode': 'ID',
                    'HierarchicalJobCategoryIds': [category_id],
                    'sortBy': 'LATEST',
                    'pageSize': 30,
                    'page': page,
                },
            },
            'query': """
            query searchJobsV3($data: JobSearchConditionInput!) {
              searchJobsV3(data: $data) {
                jobsInPage {
                  id
                  title
                  type
                  createdAt
                  educationLevel
                  minYearsOfExperience
                  maxYearsOfExperience
                  company { name }
                  location { formattedName }
                  salaries { minAmount maxAmount CurrencyCode }
                  skills { skill { name } }
                }
                hasMore
              }
            }
            """
        }
        return self.session.post(self.url, headers=self.headers, json=json_data, impersonate="chrome110", timeout=30).json()

    def fetch_description_html(self, job_id):
        url = f"https://glints.com/id/opportunities/jobs/{job_id}"
        try:
            response = self.session.get(url, headers=self.headers, impersonate="chrome110", timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                desc_div = soup.find('div', {'class': lambda x: x and 'JobDescription' in x}) or \
                           soup.find('div', {'data-testid': 'job-description'})
                if desc_div:
                    return desc_div.get_text(separator=" ").strip()
            return "N/A"
        except Exception:
            return "N/A"

# --- CONFIGURATION ---
MY_COOKIE = {
    'device_id': '0818faec-7332-40bd-9973-3dd998c4ce19',
    'g_state': '{"i_l":0,"i_ll":1781082345665,"i_e":{"enable_itp_optimization":0},"i_et":1781082339958}',
    'session': 'Fe26.2**054febbf075d47bc381c02629e0c6d0dfe0179ef2184e15035ec239a6e810e61*3S3Y00tcyJXVKwDA3TZazA*xzQa2YxNWNgL6pH1a0svakiyXNdNEl1iwo1VEQUbrWDfn7NEZEhGt6saimHBNBnq**52e16237e571a1bfc255319ad6c923a2ef0a23e7a7f264303d1b1c94c2e8b1e9*soGDH6RLExa-FJvzGlLj2E0DkKCe1Gcn-wC_Gy1O4E0',
    'traceInfo': '%7B%22expInfo%22%3A%22%22%2C%22requestId%22%3A%225dfd2ea0f651607d726bd7cd49b403ca%22%7D',
    'currentJobID': '8ace8be8-5df8-48e4-81fa-3c6aa44a7415',
    'glints_tracking_id': '6bac9f30-e693-486f-9785-1b70f4c7b8b9',
    'builderSessionId': '42e9b0ea75804176918c57a53736a513',
}

MAX_DATA_PER_CATEGORY = 990 
FILENAME = "glints_final_dataset_fast.csv"
MAX_WORKERS = 5  # Keeping it safe but saturated

csv_lock = threading.Lock()

def scrape_category(category_name, category_id):
    scraper = GlintsScraper(MY_COOKIE)
    current_page = 1
    total_collected = 0
    has_more = True
    
    print(f"[Thread-Start] 🚀 Target: {category_name}")
    
    while has_more and total_collected < MAX_DATA_PER_CATEGORY:
        data = scraper.fetch_job_list(current_page, category_id)
        
        if not data or 'data' not in data:
            break
            
        jobs = data.get('data', {}).get('searchJobsV3', {}).get('jobsInPage', [])
        if not jobs: 
            break
            
        rows_to_write = []
        for job_item in jobs:
            if total_collected >= MAX_DATA_PER_CATEGORY: 
                break
                
            # Network bound request happens here
            full_desc = scraper.fetch_description_html(job_item['id'])
            
            sal = job_item.get('salaries', [])
            salary_str = f"{sal[0]['CurrencyCode']} {sal[0]['minAmount']} - {sal[0]['maxAmount']}" if sal else "N/A"
            skills = ", ".join([s['skill']['name'] for s in job_item.get('skills', []) if s.get('skill')])

            rows_to_write.append([
                job_item.get('title'),
                job_item.get('company', {}).get('name', 'N/A'),
                job_item.get('location', {}).get('formattedName', 'N/A'),
                job_item.get('type'),
                f"{job_item.get('minYearsOfExperience', 0)}-{job_item.get('maxYearsOfExperience', 0)} years",
                job_item.get('educationLevel'),
                salary_str,
                skills,      
                full_desc,   
                job_item.get('createdAt'),
                "Glints",
                category_name
            ])
            total_collected += 1

        # 🌟 Optimization: Write the entire page batch (30 rows) at once to minimize I/O locking contention
        if rows_to_write:
            with csv_lock:
                with open(FILENAME, mode='a', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerows(rows_to_write)
        
        # 🌟 Optimization: Moved sleep to the page level. 
        # Threads sleep for 1 second AFTER finishing a batch of 30, not after every single job.
        time.sleep(1.0)

        has_more = data['data']['searchJobsV3'].get('hasMore', False)
        current_page += 1

    print(f"[Thread-Finish] ✅ {category_name} complete ({total_collected} jobs)")
    return total_collected

if __name__ == "__main__":
    with open('job_category.json', 'r', encoding='utf-8') as f:
        job_categories = json.load(f)

    file_is_empty = not os.path.exists(FILENAME) or os.path.getsize(FILENAME) == 0
    if file_is_empty:
        with open(FILENAME, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                'job_title', 'company_name', 'location', 'job_type', 
                'experience_level', 'education_req', 'salary_range', 
                'job_requirements', 'job_responsibilities', 'posted_date', 'source_platform', 'category_scraped'
            ])

    print(f"🔥 Firing up ThreadPoolExecutor with {MAX_WORKERS} workers...")
    
    start_time = time.time()
    total_platform_jobs = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_category = {
            executor.submit(scrape_category, cat_name, cat_id): cat_name 
            for cat_name, cat_id in job_categories.items()
        }
        
        for future in as_completed(future_to_category):
            category_name = future_to_category[future]
            try:
                jobs_count = future.result()
                total_platform_jobs += jobs_count
            except Exception as exc:
                print(f"💥 {category_name} generated an exception: {exc}")

    elapsed = round(time.time() - start_time, 2)
    print(f"\n🎉 SUCCESS! Scraped {total_platform_jobs} total jobs in {elapsed} seconds.")