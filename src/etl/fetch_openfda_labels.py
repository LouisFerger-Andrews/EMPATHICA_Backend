import os
import requests
import json
from requests.exceptions import HTTPError
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('OPENFDA_API_KEY', "")
BASE_URL = 'https://api.fda.gov/drug/label.json'
OUT_DIR = 'data/drugs/raw'

os.makedirs(OUT_DIR, exist_ok=True)

def fetch_openfda(limit=100, skip=0):
    params = {'limit': limit, 'skip': skip}
    if API_KEY:
        params['api_key'] = API_KEY
    r = requests.get(BASE_URL, params=params)
    try:
        r.raise_for_status()
    except HTTPError as e:
        if r.status_code == 400:
            return []
        else:
            raise
    return r.json().get('results', [])

def save_raw(data):
    for entry in data:
        rxnorm = entry.get('openfda', {}).get('rxnorm_code', ['unknown'])[0]
        set_id = entry.get('set_id', 'unknown')
        filename = f"{rxnorm}_{set_id}.json"
        path = os.path.join(OUT_DIR, filename)
        with open(path, 'w') as f:
            json.dump(entry, f, indent=2)

def main():
    skip = 0
    batch = 100
    while True:
        results = fetch_openfda(limit=batch, skip=skip)
        if not results:
            break
        save_raw(results)
        skip += len(results)

if __name__ == '__main__':
    main()
