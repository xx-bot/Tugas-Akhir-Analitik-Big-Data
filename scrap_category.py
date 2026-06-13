import json
import time
from curl_cffi import requests

url = 'https://glints.com/api/v2-alc/graphql'

# Using your verified working session configuration
cookies = {
    'device_id': '0818faec-7332-40bd-9973-3dd998c4ce19',
    'g_state': '{"i_l":0,"i_ll":1781082345665,"i_e":{"enable_itp_optimization":0},"i_et":1781082339958}',
    'session': 'Fe26.2**054febbf075d47bc381c02629e0c6d0dfe0179ef2184e15035ec239a6e810e61*3S3Y00tcyJXVKwDA3TZazA*xzQa2YxNWNgL6pH1a0svakiyXNdNEl1iwo1VEQUbrWDfn7NEZEhGt6saimHBNBnq**52e16237e571a1bfc255319ad6c923a2ef0a23e7a7f264303d1b1c94c2e8b1e9*soGDH6RLExa-FJvzGlLj2E0DkKCe1Gcn-wC_Gy1O4E0',
    'traceInfo': '%7B%22expInfo%22%3A%22%22%2C%22requestId%22%3A%225dfd2ea0f651607d726bd7cd49b403ca%22%7D',
    'currentJobID': '8ace8be8-5df8-48e4-81fa-3c6aa44a7415',
    'glints_tracking_id': '6bac9f30-e693-486f-9785-1b70f4c7b8b9',
    'builderSessionId': '42e9b0ea75804176918c57a53736a513',
}

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:150.0) Gecko/20100101 Firefox/150.0',
    'Accept': '*/*',
    'Accept-Language': 'id', # Forces Indonesian names
    'content-type': 'application/json',
    'x-glints-country-code': 'ID',
    'Origin': 'https://glints.com',
    'Connection': 'keep-alive',
}

# 1. Load the 67 categories you already found
try:
    with open('job_category.json', 'r', encoding='utf-8') as f:
        category_map = json.load(f)
    print(f"📂 Loaded job_category.json containing {len(category_map)} initial categories.")
except FileNotFoundError:
    print("❌ Could not find job_category.json. Please make sure the file exists in this directory.")
    exit()

session = requests.Session()
initial_ids = list(category_map.values())

print("🚀 Starting Deep-Discovery Loop across existing categories...")

# Loop through each category ID to reveal nested sub-subcategories
for index, cat_id in enumerate(initial_ids, start=1):
    print(f"\n🔍 [{index}/{len(initial_ids)}] Deep scanning category ID: {cat_id}")
    
    # We only need to scan the first 2 pages per category to extract the metadata properties
    for page in [1, 2]:
        json_data = {
            'operationName': 'searchJobsV3',
            'variables': {
                'data': {
                    'CountryCode': 'ID',
                    'HierarchicalJobCategoryIds': [cat_id], # Using the bulletproof parameter
                    'pageSize': 50,  
                    'page': page
                }
            },
            'query': """
            query searchJobsV3($data: JobSearchConditionInput!) {
              searchJobsV3(data: $data) {
                jobsInPage {
                  hierarchicalJobCategory {
                    id
                    name
                    parents { id name }
                  }
                }
              }
            }
            """
        }

        try:
            response = session.post(url, headers=headers, json=json_data, cookies=cookies, impersonate="chrome110", timeout=30)
            
            if response.status_code == 403:
                print("  ❌ 403 Blocked. Session token expired.")
                break
            elif response.status_code != 200:
                print(f"  ❌ Error {response.status_code}. Skipping page.")
                break
                
            search_data = response.json().get('data', {}).get('searchJobsV3', {}) or {}
            jobs = search_data.get('jobsInPage', [])
            
            if not jobs:
                break # No jobs in this category branch on this page
                
            new_found_in_page = 0
            for job in jobs:
                cat = job.get('hierarchicalJobCategory')
                if cat:
                    # Capture the sub-subcategory
                    if cat.get('name') and cat.get('id') and cat['name'] not in category_map:
                        category_map[cat['name']] = cat['id']
                        new_found_in_page += 1
                    
                    # Capture parent structures
                    for parent in cat.get('parents', []) or []:
                        if parent.get('name') and parent.get('id') and parent['name'] not in category_map:
                            category_map[parent['name']] = parent['id']
                            new_found_in_page += 1
            
            if new_found_in_page > 0:
                print(f"  📈 Page {page}: Discovered {new_found_in_page} hidden sub-categories!")
                
            time.sleep(2.0) # Respectful delay
            
        except Exception as e:
            print(f"  💥 Connection issue: {e}")
            break

# 3. Save the comprehensive, expanded map
with open('job_category.json', 'w', encoding='utf-8') as f:
    json.dump(category_map, f, indent=4, ensure_ascii=False)

print(f"\n✨ Deep Discovery finished! Total expanded list: {len(category_map)} Indonesian categories.")
print("📂 Saved completely to 'job_category.json'")