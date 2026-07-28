from plotly.io import from_json 
import streamlit as st

# formatting data to be used readily by widgets.
class ModelOutputViewData:
    def __init__(self, name:str , batch: str, id_:str, date: str, topic_map: str | None):
        self.name = name
        self.batch = batch
        self.id_ = id_
        self.date = date
        self.topic_map = from_json(topic_map) if topic_map else None


    def render_widget(self):
        ...