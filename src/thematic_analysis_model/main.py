import os
os.environ["NUMBA_THREADING_LAYER"] = "workqueue"
os.environ["NUMBA_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["TF_NUM_INTEROP_THREADS"] = "1"
os.environ["TF_NUM_INTRAOP_THREADS"] = "1"

import tensorflow as tf
tf.config.set_visible_devices([], 'GPU')

# main file
from thematic_analysis_model.model.config import *
from thematic_analysis_model.model.trial import TrialQueue
from thematic_analysis_model.model.scrape_config import alzconnected_ALL, dementiasupportforum_ALL
from thematic_analysis_model.model.dataclasses import TrialConfig, ModelOutput, Sentence
from thematic_analysis_model.model.data_management import Loader, Manager
from thematic_analysis_model.model.scraping import alzconnectedScrapingPipeline, dementiasupportforumScrapingPipeline,  ScrapingPipeline, Processor, ScrapeQueue
from thematic_analysis_model.model.embedding import Embedder
from thematic_analysis_model.model.modelling import Modeller
from thematic_analysis_model.view.visualizing import Visualizer
from thematic_analysis_model.model.validating import Validator
from thematic_analysis_model.controller.query_engine import QueryEngine

import pprint
import asyncio
import pandas as pd
import plotly.express as px


def reset_model_output():
    loader=Loader()
    db = loader.db
    db.create_table(MODEL_OUTPUT_TBL_NAME, schema=ModelOutput, mode='overwrite')

def scrape():
    loader = Loader()
    # loader.first_init() # reset on tests
    manager = Manager(loader=loader)

    ScrapeQueue(loader=loader, manager=manager, scrape_configs=dementiasupportforum_ALL) # run scrapers
    print(manager.get_num_match_condition(tbl_name='content'))
    
def process_and_embed():
    loader = Loader()
    manager = Manager(loader=loader)

    # process
    processor = Processor(manager=manager)
    processor.run_processor()

    # embed
    embedder = Embedder(loader=loader, manager=manager)
    embedder.run_embedder()

    print(manager.get_num_match_condition('sentence'))

def trial_queue_test():
    loader = Loader()
    manager = Manager(loader=loader)

    trial_configs = TrialQueue.generate_trial_configs(
        trial_name='test_parametric_hdbscan_min_samples_5_umap_n_components_5',
        batch_name='test_parametric_hdbscan_min_samples_5_umap_n_components_5',
        model_save_path=(Path('/Users/christopher.kollar/research/HealthyCityLab/DementiaForumAnalysis/thematic-analysis-model/models') / 'testing').resolve(),
        umap_parametric=True,
        hdbscan_min_cluster_size=[30, 30, 30, 30, 30],
        hdbscan_min_samples=5,
    )

    trial_queue = TrialQueue(
        loader=loader,
        manager=manager,
        trial_configs=trial_configs
    )
    trial_queue.run_queue()

def test_query_engine():
    loader=Loader()
    manager=Manager(loader=loader)
    query_engine = QueryEngine(manager=manager)
    trial_config = TrialConfig(
        trial_name='testing',
        id_='id',
        umap_parametric=True,
        hdbscan_min_cluster_size=[30, 30, 30, 30, 30, 30],
        hdbscan_min_samples=3,
    )
    [manager.add_model_output(ModelOutput(trial_config=trial_config, validation_metrics='', topic_map=None, document_map=None, heatmap=None, hierarchy_map=None)) for i in range(20)]

def main():
    loader = Loader() # loader is composed into classes that need table access directly. 
    manager=Manager(loader=loader)
    manager.clean_lancedb(0)



if __name__ == "__main__":
    main()