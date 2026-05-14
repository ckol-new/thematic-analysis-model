from thematic_analysis_model.model.queue import *
from thematic_analysis_model.model.embedding_pipeline import *
from thematic_analysis_model.model.scraping_pipeline import *
from thematic_analysis_model.model.util import *
from thematic_analysis_model.model.query import QueryEngine
from pathlib import Path
from sentence_transformers import SentenceTransformer

seeds = None # for now
seed_earlyonset = generate_seeds(base='https://alzconnected.org/categories/i-have-younger-onset-alzheimers/p', start=1, stop=10, end_seq="")
save_base = Path.cwd() / 'data'

scraping_config = {
    'seeds': seeds,
    'crawl_save_location': save_base / 'crawl_output' / 'crawl_alzconnected_livingwdementia_save1.txt',
    'scrape_save_location': save_base / 'scrape_output' / 'scrape_alzconnected_livingwdementia_save1.jsonl',
    'forum_origin': 'alzconnected'
}
embedding_config = {
    'data_location': save_base / 'scrape_output' / 'scrape_alzconnected_livingwdementia_save1.jsonl',
    'save_embeddings_location': save_base / 'embedding_output' / 'embeddings_alzconnected_livingwdementia_save1.jsonl',
    'model': SentenceTransformer('all-MiniLM-L6-v2'),
    'embedding_type': 'all-MiniLM-L6-v2'
}

scraping_config2 = {
    'seeds': seed_earlyonset,
    'crawl_save_location': save_base / 'crawl_output' / 'crawl_alzconnected_earlyonset_save1.txt',
    'scrape_save_location': save_base / 'scrape_output' / 'scrape_alzconnected_earlyonset_save1.jsonl',
    'forum_origin': 'alzconnected'
}
embedding_config2 = {
    'data_location': save_base / 'scrape_output' / 'scrape_alzconnected_earlyonset_save1.jsonl',
    'save_embeddings_location': save_base / 'embedding_output' / 'embeddings_alzconnected_earlyonset_save1.jsonl',
    'model': SentenceTransformer('all-MiniLM-L6-v2'),
    'embedding_type': 'all-MiniLM-L6-v2'
}

def pipeline_run():
    scrape_pipeline = ALZConnectedScrapingPipeline(**scraping_config2)
    embedding_pipeline = EmbeddingPipeline(**embedding_config2)

    scrape_pipeline.run_pipeline()
    embedding_pipeline.run_pipeline()

def pool():
    embedding_1_location = save_base / 'embedding_output' / 'embeddings_alzconnected_livingwdementia_save1.jsonl'
    embedding_2_location = save_base / 'embedding_output' / 'embeddings_alzconnected_earlyonset_save1.jsonl'

    scraped_1_location= save_base / 'scrape_output' / 'scrape_alzconnected_livingwdementia_save1.jsonl'
    scraped_2_location= save_base / 'scrape_output' / 'scrape_alzconnected_earlyonset_save1.jsonl'

    embedding_pooled_location = save_base / 'embedding_output' / 'embedded_pooled_test1.jsonl'
    scraped_pooled_location = save_base / 'scrape_output' / 'scraped_pooled_test1.jsonl'

    scrape_files = [scraped_1_location, scraped_2_location]
    embed_files = [embedding_1_location, embedding_2_location]

    pool_jsonl(scrape_files, scraped_pooled_location)
    pool_jsonl(embed_files, embedding_pooled_location)

def query():
    query = 'Paranoid of family members'
    model = embedding_config['model']

    embedding_pooled_location = save_base / 'embedding_output' / 'embedded_pooled_test1.jsonl'
    scraped_pooled_location = save_base / 'scrape_output' / 'scraped_pooled_test1.jsonl'
    
    query_engine = QueryEngine(model, embedding_pooled_location)
    result_dict = query_engine.run_query(query)
    result_decoded = QueryEngine.get_result_objects(result_dict, scraped_pooled_location)
    for post, sentence, similarity in result_decoded:
        print('uuid: ', post.metadata.uuid, ' sentence: ', sentence, ' similarity: ', similarity)



def main():
    query()

if __name__ == '__main__':
    main()