from pathlib import Path
from thematic_analysis_model.model.embedding_pipeline import EmbeddingPipeline
from thematic_analysis_model.model.scraping_pipeline import ScrapingPipeline
from sentence_transformers import SentenceTransformer

# model
model = SentenceTransformer('all-MiniLM-L6-v2')

def test_embedding_run_pipeline():
    # get file paths
    scrape_path = Path.cwd() / 'tests' / 'testing_data' / 'test_input_embedding_pipeline.jsonl'
    embeddings_path = Path.cwd() / 'tests' / 'testing_data' / 'test_embedding_run_pipeline.jsonl'

    # get embedding pipeline
    pipeline = EmbeddingPipeline(data_location=scrape_path, save_embeddings_location=embeddings_path, model=model, embedding_type='dense')
    embeddings = pipeline.run_pipeline()

    # test serialization/deserialization
    embeddings_loaded = EmbeddingPipeline.load_embeddings(embeddings_path)
    assert embeddings == embeddings_loaded


