from thematic_analysis_model.model.queue import *
from thematic_analysis_model.model.embedding_pipeline import *
from thematic_analysis_model.model.scraping_pipeline import *
from thematic_analysis_model.model.util import *
from pathlib import Path
from sentence_transformers import SentenceTransformer
seeds = generate_seeds(base='https://alzconnected.org/categories/i-have-alzheimers-or-other-dementia/p', start=1, stop=12, end_seq="")
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
    # 'model': SentenceTransformer('all-MiniLM-L6-v2'),
    'embedding_type': 'all-MiniLM-L6-v2'
}


def pipeline_run():
    scrape_pipeline = ALZConnectedScrapingPipeline(**scraping_config)
    embedding_pipeline = EmbeddingPipeline(**embedding_config)

    scrape_pipeline.run_pipeline()
    embedding_pipeline.run_pipeline()

def pool():
    embedding_1_location = save_base / 'embedding_output' / 'embeddings_alzconnected_livingwdementia_save1.jsonl'
    embedding_2_location = save_base / 'embedding_output' / 'embeddings_alzconnected_youngeronset_save1.jsonl'

    scraped_1_location= save_base / 'scrape_output' / 'scrape_alzconnected_livingwdementia_save1.jsonl'
    scraped_2_location= save_base / 'scrape_output' / 'scrape_alzconnected_youngeronset_save1.jsonl'

    embedding_pooled_location = save_base / 'embedding_output' / 'embedded_pooled_test1.jsonl'
    scraped_pooled_location = save_base / 'scrape_output' / 'scraped_pooled_test1.jsonl'

    scrape_files = [scraped_1_location, scraped_2_location]
    embed_files = [embedding_1_location, embedding_2_location]

    pool_jsonl(scrape_files, scraped_pooled_location)
    pool_jsonl(embed_files, embedding_pooled_location)


def main():
    scraped_pooled_location = save_base / 'scrape_output' / 'scraped_pooled_test1.jsonl'
    embedding_pooled_location = save_base / 'embedding_output' / 'embedded_pooled_test1.jsonl'
    print(line_count(scraped_pooled_location))
    print(line_count(embedding_pooled_location))

if __name__ == '__main__':
    main()