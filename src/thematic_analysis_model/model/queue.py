from thematic_analysis_model.model.scraping_pipeline import *

# pass queue class a dictionary containing all data for a given pipeline, it will instantiate it automatically and run the queue
class Queue:
    def __init__(self, pipeline_data_queue: list):
        self.scraper_options = {
            'alzconnected': ALZConnectedScrapingPipeline
        }

        self.embedder_options = {
            # insert options
        }

        pipelines = [] # instantiate queue of pipelines initatialized
        for pipeline_data in pipeline_data_queue:
            pipeline = None

            # load pipeline of respective type and forum specificity
            if pipeline_data.get['type'] == 'scraper':
                try:
                    pipeline = self.scraper_options.get(pipeline_data.get('forum'))(
                        pipeline_data.get('seeds'), 
                        pipeline_data.get('crawl_save_location'),
                        pipeline_data.get('scrape_save_location')
                        )
                except: continue # move on to next pipeline if issue

            pipelines.append()

        for pipeline in pipelines:
            pipeline.run_pipeline() # run pipeline
        


        



