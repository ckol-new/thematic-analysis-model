import lancedb as ldb
from sentence_transformers import SentenceTransformer
from thematic_analysis_model.config import base, LDB_PATH, SCRAPE_DATA_TABLE_NAME, embedding_model, umap_model, hdbscan_model, vectorizer_model
from thematic_analysis_model.model.dclasses import Content, SchemaContent
from thematic_analysis_model.model.scraping_pipeline import ALZConnectedScrapingPipeline, ScrapingPipeline
from thematic_analysis_model.model.embedding_pipeline import EmbeddingPipeline
from thematic_analysis_model.model.topic_modeller import TopicModeller
import pandas as pd
from bertopic import BERTopic
from pathlib import Path

def main():
    db = ldb.connect('lance_db')
    sentence_tbl = db.open_table('sentence_data_table')

    '''
    topic_modeller = TopicModeller(
        embedding_model=embedding_model,
        vectorizer_model=vectorizer_model,
        umap_model=umap_model,
        hdbscan_model=hdbscan_model
    )
    
    TopicModeller.reset_model_flag(sentence_tbl)
    spath = base / 'test_topic_model'
    topic_modeller.run_model(sentence_tbl, spath)

    spath = base / 'test_topic_model'
    merged_model = TopicModeller.load_merged_model(spath)

    '''

    mpath = Path.cwd() / 'test_topic_model'
    model = BERTopic.load(mpath)
    fig = model.visualize_topics()
    fig.write_html('bertopics_pre-finetuning.html')
    fig.show()




    










    


if __name__ == '__main__':
    main()