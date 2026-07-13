# all classes around modelling
import pandas as pd
import lancedb
from pathlib import Path

from bertopic import BERTopic 

class Modeller:
    def __init__(self, tbl: lancedb.Table, topic_model: BERTopic):
        self.tbl = tbl
        self.topic_model = topic_model

    # merge in batches, merge submodels, return merged model
    def model(self) -> BERTopic:
        # baseline model (empty)
        baseline_model = self.topic_model

        # shuffle ids to model

        # for each batch
            # copy baseline
            # model batch
            # update bools

            # if num of submodels too high, merge

            # serialize submodels every interval

        # 
        return

    # model batch return sub model
    # update bools
    def model_batch(self, batch: pd.DataFrame):
        return 

    @classmethod
    def save_model(self, model: BERTopic):
        ...

    @classmethod
    def load_model(self, path: Path) -> BERTopic:
        return 

class Validator:
    ...