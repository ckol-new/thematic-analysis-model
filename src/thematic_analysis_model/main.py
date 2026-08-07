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
from thematic_analysis_model.model.dataclasses import TrialConfig, ModelOutput, Sentence, model_output_adapter
from thematic_analysis_model.model.data_management import Loader, Manager
from thematic_analysis_model.model.scraping import alzconnectedScrapingPipeline, dementiasupportforumScrapingPipeline,  ScrapingPipeline, Processor, ScrapeQueue
from thematic_analysis_model.model.embedding import Embedder
from thematic_analysis_model.model.modelling import Modeller
from thematic_analysis_model.view.visualizing import Visualizer
from thematic_analysis_model.model.validating import Validator, StabilityEvaluator
from thematic_analysis_model.controller.query_engine import QueryEngine

import pprint
import asyncio
import pandas as pd
import plotly.express as px
import json


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
        trial_name='test_batch_hdbscan_min_samples_5_',
        batch_name='test_stability_3_DIFF',
        model_save_path=(Path('/Users/christopher.kollar/research/HealthyCityLab/DementiaForumAnalysis/thematic-analysis-model/models') / 'testing').resolve(),
        umap_parametric=True,
        hdbscan_min_cluster_size=[30, 30, 30, 30],
        hdbscan_min_samples=5,
    )

    trial_queue = TrialQueue(
        loader=loader,
        manager=manager,
        trial_configs=trial_configs
    )
    trial_queue.run_queue()

def test_stability_metrics():
    loader = Loader()
    manager = Manager(loader)
    stability_validator = StabilityEvaluator(
        loader=loader, manager=manager
    )

    d = stability_validator.evaluate('test_stability_3_DIFF')
    pprint.pprint(d, sort_dicts=False)
    
def main():
    loader = Loader() # loader is composed into classes that need table access directly. 
    tbl = loader.connect(MODEL_OUTPUT_TBL_NAME)
    mo =  tbl.search().limit(1).to_pydantic(model=ModelOutput)[0]
    pprint.pprint(json.loads(mo.topic_vectors))

    '''
    json_str = model_output_adapter.dump_json(mo, indent=4).decode('utf-8')

    print('a')
    p = Path.cwd() / 'test_mo' / 'test.json'
    with p.open('w', encoding='utf-8') as f:
        f.write(json_str)

    print('b')
    '''

    
    


if __name__ == "__main__":
    main()