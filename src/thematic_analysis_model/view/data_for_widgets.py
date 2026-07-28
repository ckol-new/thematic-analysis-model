from thematic_analysis_model.model.dataclasses import ModelOutput

from plotly.io import from_json 
import streamlit as st

# formatting data to be used readily by widgets.
class ModelOutputSearchBarViewData:
    def __init__(self, name:str , batch: str, id_:str, date: str, topic_map: str | None, model_output: ModelOutput):
        self.name = name
        self.batch = batch
        self.id_ = id_
        self.date = date
        self.topic_map = from_json(topic_map) if topic_map else None
        self.model_output = model_output


    def render_widget(self):
        ...

class ModelOutputViewData:
    def __init__(self, model_output: ModelOutput):
        self.model_output = model_output
    