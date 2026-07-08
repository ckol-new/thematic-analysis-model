import os

# 1. Increase the absolute memory limit DataFusion is allowed to use.
# Change "12G" to whatever fits your system (e.g., "8G", "16G", "32G")
os.environ["DATAFUSION_RUNTIME_MEMORY_LIMIT"] = "4G"

# 2. Decrease the spill reservation size (in bytes). 
# This forces the sorter to start spilling data chunks to your disk 
# much earlier instead of trying to hold massive blocks in RAM.
os.environ["DATAFUSION_EXECUTION_SORT_SPILL_RESERVATION_BYTES"] = str(512 * 1024 * 1024)  # 512 MB

import lancedb
import pyarrow as pa
from pathlib import Path
from thematic_analysis_model.model.dclasses import SchemaContent, SchemaSentence
from thematic_analysis_model.model.scraping_pipeline import ScrapingPipeline, ALZConnectedScrapingPipeline, AlzSocietyDementiaSupportForum
from thematic_analysis_model.model.embedding_pipeline import EmbeddingPipeline
from thematic_analysis_model.model.modelling_pipeline import TopicModeller
import asyncio
import random
from sentence_transformers import SentenceTransformer
from bertopic import BERTopic
from sklearn.decomposition import IncrementalPCA
from umap import UMAP
from hdbscan import HDBSCAN
from sklearn.cluster import MiniBatchKMeans
from bertopic.vectorizers import OnlineCountVectorizer

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
umap_model = UMAP()
minibatchkmeans_model = MiniBatchKMeans()
hdbscan_model = HDBSCAN(min_cluster_size=20, min_samples=15)
count_vectorizer = OnlineCountVectorizer(stop_words='english')
topic_model = BERTopic(
    embedding_model=embedding_model,
    umap_model=umap_model,
    hdbscan_model=hdbscan_model,
    vectorizer_model=count_vectorizer,
    calculate_probabilities=True
)

def main():
    db = lancedb.connect('split_db')

    stbl = db.open_table('split_sentence')

    print(stbl.count_rows(filter='is_modelled = false'))

    save_path = Path.cwd() / 'topics_model_save' / 'test.pkl'
    TopicModeller.reset_flags(stbl)
    print(stbl.count_rows(filter='is_modelled = false'))

    merged_model = TopicModeller.run_pipeline(
        tbl=stbl,
        spath=save_path,
        model=topic_model
    )

    fig = merged_model.visualize_topics()
    fig.show()

def split_data():
    db = lancedb.connect('database')
    stbl = db.open_table('sentence')

    shuffled_ids = TopicModeller.shuffle(stbl)
    sample_ids = shuffled_ids[0:500000]

    new_tbl = stbl.take_row_ids(sample_ids).to_arrow()

    new_db = lancedb.connect('split_db')
    new_db.create_table('split_sentence', new_tbl)

    




def main1():
    db = lancedb.connect('database')

    '''
    tbl = db.create_table('content', schema=SchemaContent, mode='overwrite')
    stbl = db.create_table('sentence', schema=SchemaSentence, mode='overwrite')
    tbl.create_scalar_index('url_hash')
    stbl.create_scalar_index('sentence_hash')
    '''

    tbl = db.open_table('content')
    stbl = db.open_table('sentence')

    print(tbl.count_rows())
    print(stbl.count_rows())

    model = SentenceTransformer('all-MiniLM-L6-v2', device='mps')
    ep = EmbeddingPipeline()
    ep.run_embedding_pipeline(
        stbl, model
    )

    '''
    for forum in DementiaSupportForum:
        print(f"PROCESSING {forum['origin']}")
        asyncio.run(
            forum['scraper'].run_pipeline(
                table=tbl,
                origin=forum['origin']
            )
        )

        embed_pipeline = EmbeddingPipeline()
        embed_pipeline.run_processing_pipeline(
            tbl, stbl
        )
    '''

    print(tbl.count_rows())
    print(stbl.count_rows())

def main2():
    db = lancedb.connect('database')

    tbl = db.open_table('content')
    stbl = db.open_table('sentence')

    stbl.alter_columns({
        'path': 'new_list_col',
        'rename': 'probabilities'
    })


    print(stbl.schema)



if __name__ == '__main__':
    main()