import lancedb as ldb
# from sentence_transformers import SentenceTransformer
# from thematic_analysis_model.config import base, LDB_PATH, SCRAPE_DATA_TABLE_NAME, embedding_model, umap_model, hdbscan_model, vectorizer_model
from thematic_analysis_model.model.dclasses import SchemaSentence, SchemaContent
from thematic_analysis_model.model.scraping_pipeline import ALZConnectedScrapingPipeline, ScrapingPipeline
from thematic_analysis_model.model.embedding_pipeline import EmbeddingPipeline
from thematic_analysis_model.model.topic_modeller import TopicModeller
import pandas as pd
# from bertopic import BERTopic
from pathlib import Path
import hashlib



def main():
    db = ldb.connect('db')
    tbl = db.create_table('content', schema=SchemaContent)
    stbl = db.create_table('sentence', schema=SchemaSentence)

    print(tbl.schema)
    print(stbl.schema)



if __name__ == '__main__':
    main()