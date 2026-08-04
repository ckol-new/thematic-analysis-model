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
    def handle_input(self, text:str) -> str | None:
        if not text:
            return self.query_db(None)
        text = text.rstrip() # remove whitespace
        if not text:
            return self.query_db(None)

        # check if parameter search or not
        if '=' not in text:
            return self.query_db(text, semantic_search=True)

        # check search mode
        search_prefix: str = ""
        dtype = None # type of data that we are querying
        for key, val in self.search_mode_dict.items():
            if text.startswith(key):
                # get text
                search_prefix = val
                text = re.sub(pattern=key, repl="", string=text)
                text = text.rstrip()

                # get dtype
                #   remove '=' from key, to get field name, get annotated data type
                dtype = TrialConfig.model_fields[key.replace('=', '')].annotation

                if dtype == str:
                    condition = search_prefix + f' = "{text}"'
                    return self.query_db(condition=condition)
                elif dtype == int:
                    condition = search_prefix + f' = {text}'
                    return self.query_db(condition=condition)
                elif dtype == float:
                    condition = search_prefix + f' = {text}'
                    return self.query_db(condition=condition)
                elif dtype == bool:
                    condition = search_prefix + f' IS {text.upper()}'
                    return self.query_db(condition=condition)

        condition = f'trial_config.trial_name = "{text}"' # this only works for 
        return self.query_db(condition, semantic_search=False)

    # query database, returns list of model outputs
    #   query must be pasedm after .handle_input() processes user input
    def query_db(self, condition: str, semantic_search: bool = False) -> list[ModelOutput]:
        return self.manager.get_model_output(condition=condition, semantic_search=semantic_search)