# main file
from thematic_analysis_model.model.config import *
from thematic_analysis_model.model.scrape_config import alzconnected_ALL, dementiasupportforum_ALL
from thematic_analysis_model.model.dataclasses import TrialConfig, ModelOutput
from thematic_analysis_model.model.data_management import Loader, Manager
from thematic_analysis_model.model.scraping import alzconnectedScrapingPipeline, dementiasupportforumScrapingPipeline,  ScrapingPipeline, Processor, ScrapeQueue
from thematic_analysis_model.model.embedding import Embedder
from thematic_analysis_model.model.modelling import Modeller
from thematic_analysis_model.view.visualizing import Visualizer
from thematic_analysis_model.model.validating import Validator

import pprint
import asyncio
import plotly


def reset_model_output():
    loader=Loader()
    db = loader.db
    db.create_table(MODEL_OUTPUT_TBL_NAME, schema=ModelOutput, mode='overwrite')

def scrape():
    loader = Loader()
    # loader.first_init() # reset on tests
    manager = Manager(loader=loader)

    ScrapeQueue(loader=loader, manager=manager, scrape_configs=alzconnected_ALL) # run scrapers

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

def model_and_validate():
    loader = Loader()
    manager= Manager(loader=loader)
    manager.reset_modelling_flags()
    manager.clean_lancedb()

    trial_config = TrialConfig(
        trial_name='testing',
        id_='id',
        trial_num=1,
        umap_parametric=False,
        umap_n_neighbours=30,
        umap_n_components=5,
        hdbscan_min_cluster_size=30,
        hdbscan_min_samples=5,
    )

    # model
    modeller = Modeller(
        loader=loader,
        manager=manager,
        trial_config=trial_config
    )
    model = modeller.run_modeller(save_reduced_embeddings=True)
    model_path_test = Path.cwd() / 'test_model' / 'test'
    manager.save_model(path=model_path_test, model=model)
    loaded_model = manager.load_model(path=model_path_test)

    # valdiate
    visualizer = Visualizer(manager=manager)
    validator = Validator(model=loaded_model, loader=loader, manager=manager, visualizer=visualizer, trial_config=trial_config)
    model_output = validator.run_validator()
    print('rendering')
    topic_map = plotly.io.from_json(model_output.topic_map, engine='json')
    topic_map.show()

def validate():
    loader = Loader()
    manager = Manager(loader=loader)
    manager.clean_lancedb()
    manager.reset_validation_flags()

    model_path_test = Path.cwd() / 'test_model' / 'test'
    loaded_model = manager.load_model(path=model_path_test)

    trial_config = TrialConfig(
        trial_name='testing',
        id_='id',
        trial_num=1,
        umap_parametric=False,
        umap_n_neighbours=30,
        umap_n_components=5,
        hdbscan_min_cluster_size=30,
        hdbscan_min_samples=5,
    )
    visualizer = Visualizer(manager=manager)
    validator = Validator(model=loaded_model, loader=loader, manager=manager, visualizer=visualizer, trial_config=trial_config)
    mo = validator.run_validator()
    plotly.io.from_json(mo.topic_map, engine='json').show()





def main():
    loader = Loader() # loader is composed into classes that need table access directly. 
    manager = Manager(loader=loader) # manager gives classes access to the table, to update or retrieve data.






if __name__ == "__main__":
    model_and_validate()
    
