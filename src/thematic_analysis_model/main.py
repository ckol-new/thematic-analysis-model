import lancedb as ldb
from thematic_analysis_model.config import LDB_PATH, SCRAPE_DATA_TABLE_NAME
from thematic_analysis_model.model.dclasses import Content

def main():
    db = ldb.connect(LDB_PATH)
    table = db.open_table(SCRAPE_DATA_TABLE_NAME)


if __name__ == '__main__':
    main()