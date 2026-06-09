import lancedb as ldb
# from sentence_transformers import SentenceTransformer
# from thematic_analysis_model.config import base, LDB_PATH, SCRAPE_DATA_TABLE_NAME, embedding_model, umap_model, hdbscan_model, vectorizer_model
from thematic_analysis_model.model.dclasses import Content, SchemaContent
from thematic_analysis_model.model.scraping_pipeline import ALZConnectedScrapingPipeline, ScrapingPipeline
from thematic_analysis_model.model.embedding_pipeline import EmbeddingPipeline
from thematic_analysis_model.model.topic_modeller import TopicModeller
import pandas as pd
# from bertopic import BERTopic
from pathlib import Path
import hashlib

# temp
def normalize_url(url: str) -> str:
    # strip
    url = url.strip()

    # lowercase
    url = url.lower()
    
    return url

def generate_hash(url: str) -> str:
    url = normalize_url(url)
    return hashlib.sha256(url.encode('utf-8')).digest()

def rehash_db(tbl: ldb.Table, batch_size: int = 5000):
    uuids = tbl.search().select(['uuid']).to_pandas()['uuid'].to_list()
    total = tbl.count_rows()
    for i in range(0, total, batch_size):
        uuid_todo = uuids[i:i+batch_size]

        
        query = ','.join(map(str, uuid_todo))
        df = tbl.search().where(f"uuid IN ({query})").select(['url']).to_pandas()
        urls = df['url'].to_list()
        del df
        hashes = []
        for url in urls:
            hashes.append(generate_hash(url))
        del urls

        upsert_dict = [
            {
                'uuid': uid,
                'url_hash': str(url_hash)
            } for uid, url_hash in zip(uuid_todo, hashes)
        ]
        (
            tbl.merge_insert(on='uuid')
            .when_matched_update_all()
            .execute(upsert_dict)
            
        )


    



def main():
    db = ldb.connect('lance_db')
    post_tbl = db.open_table('scrape_content')
    sentence_tbl = db.open_table('sentence_data_table')

    print(post_tbl.schema)

    rehash_db(post_tbl)




    










    


if __name__ == '__main__':
    main()