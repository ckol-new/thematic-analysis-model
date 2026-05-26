import lancedb as ldb
from sentence_transformers import SentenceTransformer
from thematic_analysis_model.config import LDB_PATH, SCRAPE_DATA_TABLE_NAME, schema
from thematic_analysis_model.model.dclasses import Content, SchemaContent
from thematic_analysis_model.model.scraping_pipeline import ALZConnectedScrapingPipeline, ScrapingPipeline
from thematic_analysis_model.model.embedding_pipeline import EmbeddingPipeline
import pandas as pd

def main():
    db = ldb.connect('lance_db')
    scraped_tbl = db.open_table('scrape_content')
    sentence_tbl = db.open_table('sentence_data_table')

    question = 'Scam calls'
    model = SentenceTransformer('all-MiniLM-L6-v2')
    result = sentence_tbl.search(model.encode(question)).select(['sentence', 'url']).to_pandas()
    print(result.head(100))








    


if __name__ == '__main__':
    main()