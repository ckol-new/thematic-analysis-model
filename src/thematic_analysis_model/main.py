import lancedb as ldb
from sentence_transformers import SentenceTransformer
from thematic_analysis_model.config import LDB_PATH, SCRAPE_DATA_TABLE_NAME, schema
from thematic_analysis_model.model.dclasses import Content, SchemaContent
from thematic_analysis_model.model.scraping_pipeline import ALZConnectedScrapingPipeline, ScrapingPipeline
from thematic_analysis_model.model.embedding_pipeline import EmbeddingPipeline
import pandas as pd

def main():
    db = ldb.connect('lance_db')
    sentence_tbl = db.open_table('sentence_data_table')









    


if __name__ == '__main__':
    main()