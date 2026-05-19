from thematic_analysis_model.model.util import *
from thematic_analysis_model.model.dclasses import *
from thematic_analysis_model.model.scraping_pipeline import *
from thematic_analysis_model.model.embedding_pipeline import *
from thematic_analysis_model.model.query import *
from pathlib import Path
from sentence_transformers import SentenceTransformer

# Data common
base = Path.cwd() / 'data'
common_data = {
    'crawl_output_base': base / 'crawl_output',
    'scrape_output_base': base / 'scrape_output',
    'embedding_output_base': base / 'embedding_output',
    'model': SentenceTransformer('all-MiniLM-L6-v2'),
    'pooled_embedding_output': base / 'embeddings_pooled.jsonl',
    'pooled_scraped_output': base / 'scrape_pooled.jsonl'
}

# caregiver general
caregiver_general_scraper1_50 = {
    'seeds': generate_seeds(base='https://alzconnected.org/categories/i-am-a-caregiver-(general-topics)/p', start=1, stop=50, end_seq=""),
    'crawl_save_location': common_data['crawl_output_base'] / 'crawl_alzconnected_caregivergeneral_1_50_save1.txt',
    'scrape_save_location': common_data['scrape_output_base'] / 'scrape_alzconnected_caregivergeneral_1_50_save1.jsonl',
    'forum_origin': 'alzconnected'
}
caregiver_general_embedder1_50 = {
    'data_location': caregiver_general_scraper1_50['scrape_save_location'],
    'save_embeddings_location': common_data['embedding_output_base'] / 'embeddings_alzconnected_caregivergeneral_1_50_save1.jsonl',
    'model': common_data['model'],
    'embedding_type': 'all-MiniLM-L6-v2'
}
caregiver_general_scraper51_100 = {
    'seeds': generate_seeds(base='https://alzconnected.org/categories/i-am-a-caregiver-(general-topics)/p', start=51, stop=100, end_seq=""),
    'crawl_save_location': common_data['crawl_output_base'] / 'crawl_alzconnected_caregivergeneral_51_100_save1.txt',
    'scrape_save_location': common_data['scrape_output_base'] / 'scrape_alzconnected_caregivergeneral_51_100_save1.jsonl',
    'forum_origin': 'alzconnected'
}
caregiver_general_embedder51_100 = {
    'data_location': caregiver_general_scraper51_100['scrape_save_location'],
    'save_embeddings_location': common_data['embedding_output_base'] / 'embeddings_alzconnected_caregivergeneral_51_100_save1.jsonl',
    'model': common_data['model'],
    'embedding_type': 'all-MiniLM-L6-v2'
}
caregiver_general_scraper101_150 = {
    'seeds': generate_seeds(base='https://alzconnected.org/categories/i-am-a-caregiver-(general-topics)/p', start=101, stop=150, end_seq=""),
    'crawl_save_location': common_data['crawl_output_base'] / 'crawl_alzconnected_caregivergeneral_101_150_save1.txt',
    'scrape_save_location': common_data['scrape_output_base'] / 'scrape_alzconnected_caregivergeneral_101_150_save1.jsonl',
    'forum_origin': 'alzconnected'
}
caregiver_general_embedder101_150 = {
    'data_location': caregiver_general_scraper101_150['scrape_save_location'],
    'save_embeddings_location': common_data['embedding_output_base'] / 'embeddings_alzconnected_caregivergeneral_101_150_save1.jsonl',
    'model': common_data['model'],
    'embedding_type': 'all-MiniLM-L6-v2'
}
caregiver_general_scraper151_192 = {
    'seeds': generate_seeds(base='https://alzconnected.org/categories/i-am-a-caregiver-(general-topics)/p', start=151, stop=192, end_seq=""),
    'crawl_save_location': common_data['crawl_output_base'] / 'crawl_alzconnected_caregivergeneral_151_192_save1.txt',
    'scrape_save_location': common_data['scrape_output_base'] / 'scrape_alzconnected_caregivergeneral_151_192_save1.jsonl',
    'forum_origin': 'alzconnected'
}
caregiver_general_embedder151_192 = {
    'data_location': caregiver_general_scraper151_192['scrape_save_location'],
    'save_embeddings_location': common_data['embedding_output_base'] / 'embeddings_alzconnected_caregivergeneral_151_192_save1.jsonl',
    'model': common_data['model'],
    'embedding_type': 'all-MiniLM-L6-v2'
}

# caregiver for spouse or partner forum
caregiver_partner_scraper1_50 = {
    'seeds': generate_seeds(base='https://alzconnected.org/categories/spouses-or-partners/p', start=1, stop=50, end_seq=''),
    'crawl_save_location': common_data['crawl_output_base'] / 'crawl_alzconnected_caregiver_partner_1_50_save1.txt',
    'scrape_save_location': common_data['scrape_output_base'] / 'scrape_alzconnected_caregiver_partner_1_50_save1.jsonl',
    'forum_origin': 'alzconnected'
}
caregiver_partner_embedder1_50 = {
    'data_location': caregiver_partner_scraper1_50['scrape_save_location'],
    'save_embeddings_location': common_data['embedding_output_base'] / 'embeddings_alzconnected_caregiver_partner_1_50_save1.jsonl',
    'model': common_data['model'],
    'embedding_type': 'all-MiniLM-L6-v2'
}

caregiver_partner_scraper51_100 = {
    'seeds': generate_seeds(base='https://alzconnected.org/categories/spouses-or-partners/p', start=51, stop=100, end_seq=''),
    'crawl_save_location': common_data['crawl_output_base'] / 'crawl_alzconnected_caregiver_partner_51_100_save1.txt',
    'scrape_save_location': common_data['scrape_output_base'] / 'scrape_alzconnected_caregiver_partner_51_100_save1.jsonl',
    'forum_origin': 'alzconnected'
}
caregiver_partner_embedder51_100 = {
    'data_location': caregiver_partner_scraper51_100['scrape_save_location'],
    'save_embeddings_location': common_data['embedding_output_base'] / 'embeddings_alzconnected_caregiver_partner_51_100_save1.jsonl',
    'model': common_data['model'],
    'embedding_type': 'all-MiniLM-L6-v2'
}


# caregiver for parent forum
caregiver_parent_scraper1_50 = {
    'seeds': generate_seeds(base='https://alzconnected.org/categories/caring-for-a-parent/p', start=1, stop=50, end_seq=''),
    'crawl_save_location': common_data['crawl_output_base'] / 'crawl_alzconnected_caregiver_parent_1_50_save1.txt',
    'scrape_save_location': common_data['scrape_output_base'] / 'scrape_alzconnecated_caregiver_parent_1_50_save1.jsonl',
    'forum_origin': 'alzconnected'
}
caregiver_parent_embedder1_50 = {
    'data_location': caregiver_partner_scraper1_50['scrape_save_location'],
    'save_embeddings_location': common_data['embedding_output_base'] / 'embeddings_alzconnected_caregiver_parent_1_50_save1.jsonl',
    'model': common_data['model'],
    'embedding_type': 'all-MiniLM-L6-v2'
}

caregiver_parent_scraper51_100 = {
    'seeds': generate_seeds(base='https://alzconnected.org/categories/caring-for-a-parent/p', start=51, stop=100, end_seq=''),
    'crawl_save_location': common_data['crawl_output_base'] / 'crawl_alzconnected_caregiver_parent_51_100_save1.txt',
    'scrape_save_location': common_data['scrape_output_base'] / 'scrape_alzconnected_caregiver_parent_51_100_save1.jsonl',
    'forum_origin': 'alzconnected'
}
caregiver_parent_embedder51_100 = {
    'data_location': caregiver_partner_scraper51_100['scrape_save_location'],
    'save_embeddings_location': common_data['embedding_output_base'] / 'embeddings_alzconnected_caregiver_parent_51_100_save1.jsonl',
    'model': common_data['model'],
    'embedding_type': 'all-MiniLM-L6-v2'
}