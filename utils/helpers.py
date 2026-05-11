import json
import csv
import time
import random
import logging
import glob
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/llm4crypto.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def save_to_json(data: List[Dict[str, Any]], filepath: str) -> None:
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_from_json(filepath: str) -> List[Dict[str, Any]]:
    if '*' in filepath or '?' in filepath:
        files = glob.glob(filepath)
        if not files:
            return []
        filepath = max(files, key=os.path.getctime)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except Exception as e:
        logger.error(f"Failed to load JSON file {filepath}: {e}")
        return []

def save_to_csv(data: List[Dict[str, Any]], filepath: str) -> None:
    if not data:
        return
    fieldnames = data[0].keys()
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def load_from_csv(filepath: str) -> List[Dict[str, Any]]:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    except FileNotFoundError:
        return []

def random_delay(min_delay: float = 1.0, max_delay: float = 3.0) -> None:
    time.sleep(random.uniform(min_delay, max_delay))

def get_current_utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()

def convert_to_utc(dt_str: str, format_str: str = '%Y-%m-%dT%H:%M:%S') -> str:
    try:
        dt = datetime.strptime(dt_str, format_str)
        return dt.replace(tzinfo=timezone.utc).isoformat()
    except ValueError:
        return dt_str

def generate_unique_id() -> str:
    return f"{int(time.time())}_{random.randint(1000, 9999)}"

def truncate_text(text: str, max_length: int = 5000) -> str:
    return text[:max_length] + '...' if len(text) > max_length else text

def remove_duplicates(data: List[Dict[str, Any]], key: str = 'id') -> List[Dict[str, Any]]:
    seen = set()
    result = []
    for item in data:
        item_key = item.get(key, generate_unique_id())
        if item_key not in seen:
            seen.add(item_key)
            result.append(item)
    return result