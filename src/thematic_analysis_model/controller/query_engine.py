from ..model.data_management import Manager
from ..model.dataclasses import TrialConfig, ModelOutput

from dataclasses import fields
import re

# class for handling user queries into database


class QueryEngine:
    search_mode_dict = {
        str(field_name) + '=': f"trial_config.{str(field_name)}" for field_name in TrialConfig.model_fields
    }
    def __init__(self, manager: Manager):
        self.manager = manager

    # input handling
    #   for side bar input, outputs query needed for lancedb
    def handle_input(self, text:str) -> str:
        text = text.rstrip() # remove whitespace

        # check search mode
        search_prefix: str = ""
        for key, val in self.search_mode_dict.items():
            if text.startswith(key):
                search_prefix = val
                text = re.sub(pattern=key, repl="", string=text)
                return search_prefix + f' = "{text}"'

        condition = f'trial_config.trial_name = "{text}"' # this only works for 
        return condition

    # query database, returns list of model outputs
    #   query must be pasedm after .handle_input() processes user input
    def query_db(self, condition: str) -> list[ModelOutput]:
        return self.manager.get_model_output(condition=condition)