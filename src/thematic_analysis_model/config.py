from pathlib import Path
base = Path.cwd()

LDB_PATH = base / 'lance_db'
SCRAPE_DATA_TABLE_NAME = 'scrape_data'


# BATCH SIZES
SCRAPING_BATCH_SIZE = 10000