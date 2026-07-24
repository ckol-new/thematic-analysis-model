# main file
from thematic_analysis_model.model.config import *
from thematic_analysis_model.model.scrape_config import alzconnected_ALL, dementiasupportforum_ALL
from thematic_analysis_model.model.dataclasses import TrialConfig
from thematic_analysis_model.model.data_management import Loader, Manager
from thematic_analysis_model.model.scraping import alzconnectedScrapingPipeline, dementiasupportforumScrapingPipeline,  ScrapingPipeline, Processor, ScrapeQueue
from thematic_analysis_model.model.embedding import Embedder
from thematic_analysis_model.model.modelling import Modeller
from thematic_analysis_model.view.visualizing import Visualizer
from thematic_analysis_model.model.validating import Validator

import pprint
import asyncio

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

    # model
    modeller = Modeller(
        loader=loader,
        manager=manager,
        trial_config=None
    )
    model = modeller.run_modeller(save_reduced_embeddings=True)
    model_path_test = Path.cwd() / 'test_model' / 'test'
    manager.save_model(path=model_path_test, model=model)
    loaded_model = manager.load_model(path=model_path_test)

    # valdiate
    visualizer = Visualizer(manager=manager)
    validator = Validator(model=loaded_model, loader=loader, manager=manager, visualizer=visualizer, trial_config=None)
    validation_metrics, topic_map, doc_map, heatmap, hierarchy_map = validator.run_validator()
    topic_map.show()
    doc_map.show()





def main():
    loader = Loader() # loader is composed into classes that need table access directly. 
    manager = Manager(loader=loader) # manager gives classes access to the table, to update or retrieve data.
    print(manager.get_num_match_condition('sentence', condition='is_modelled = false'))
    print(manager.get_num_match_condition('sentence', condition='is_modelled = true'))
    print(loader.connect('sentence').search().select(['sentence', 'is_modelled', 'is_validated']).to_pandas().head(1000))





if __name__ == "__main__":
    model_and_validate()
