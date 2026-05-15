from thematic_analysis_model.model.queue import *
from thematic_analysis_model.model.embedding_pipeline import *
from thematic_analysis_model.model.scraping_pipeline import *
from thematic_analysis_model.model.util import *
from thematic_analysis_model.model.query import QueryEngine
from pathlib import Path
from sentence_transformers import SentenceTransformer

from thematic_analysis_model.pipeline_config.alzconnected import *

def pipelinex():
    s_pipeline = ALZConnectedScrapingPipeline(**caregiver_general_scraper1_50)
    e_pipeline = EmbeddingPipeline(**caregiver_general_embedder1_50)
    s_pipeline.run_pipeline()
    e_pipeline.run_pipeline()

def pipeline1():
    # scrape 1-50
    print("STARTING 1-50")
    try: 
        s_pipeline = ALZConnectedScrapingPipeline(**caregiver_general_scraper1_50)
        e_pipeline = EmbeddingPipeline(**caregiver_general_embedder1_50)
    except: ...
    try: s_pipeline.run_pipeline()
    except Exception as e: 
        print(f'Cannot run scraping pipeline {e}')
        raise Exception(e)
    try: e_pipeline.run_pipeline()
    except Exception as e: 
        print(f'Cannot run embedding pipeline {e}')
        raise Exception(e)

    print("SCRAPING 51-100")
    # scrape 51-100
    try: 
        s_pipeline = ALZConnectedScrapingPipeline(**caregiver_general_scraper51_100)
        e_pipeline = EmbeddingPipeline(**caregiver_general_embedder51_100)
    except: ...
    try: s_pipeline.run_pipeline()
    except: ...
    try: e_pipeline.run_pipeline()
    except: ...


def pipeline2():
    print("SCRAPING 101-150")
    # scrape 101-150
    try: 
        s_pipeline = ALZConnectedScrapingPipeline(**caregiver_general_scraper101_150)
        e_pipeline = EmbeddingPipeline(**caregiver_general_embedder101_150)
    except: ...
    try: s_pipeline.run_pipeline()
    except: ...
    try: e_pipeline.run_pipeline()
    except: ...
    
    print("SCRAPING 151-192")
    # scrape 151-192
    try: 
        s_pipeline = ALZConnectedScrapingPipeline(**caregiver_general_scraper151_192)
        e_pipeline = EmbeddingPipeline(**caregiver_general_embedder151_192)
    except: ...
    try: s_pipeline.run_pipeline()
    except: ...
    try: e_pipeline.run_pipeline()
    except: ...

def query():
    query = 'Paranoid of family members'
    model = common_data['model']

    embedding_pooled_location = save_base / 'embedding_output' / 'embedded_pooled_test1.jsonl'
    scraped_pooled_location = save_base / 'scrape_output' / 'scraped_pooled_test1.jsonl'
    
    query_engine = QueryEngine(model, embedding_pooled_location)
    result_dict = query_engine.run_query(query)
    result_decoded = QueryEngine.get_result_objects(result_dict, scraped_pooled_location)
    for post, sentence, similarity in result_decoded:
        print('uuid: ', post.metadata.uuid, ' sentence: ', sentence, ' similarity: ', similarity)



def main():
    

if __name__ == '__main__':
    main()