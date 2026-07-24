from thematic_analysis_model.model.data_management import Manager
from thematic_analysis_model.model.config import SENTENCE_TBL_NAME

from bertopic import BERTopic
import numpy as np
import plotly as pl
from plotly.graph_objs import Figure

# visualizing validated models
#   while it uses the model to generate some figures, it does not own it as a field in order to make it more flexible for when it interacts with the data app itself.
class Visualizer:
    def __init__(self, manager: Manager):
        self.manager = manager

    def visualize_topic_map(self, model: BERTopic) -> Figure:
        return model.visualize_topics()

    def visualize_topic_heatmap(self, model: BERTopic) -> Figure:
        return model.visualize_heatmap()

    def visualize_topic_hierarchy(self, model: BERTopic) -> Figure:
        return model.visualize_hierarchy()

    def visualize_document_map(self, model: BERTopic, manager: Manager) -> Figure:
        docs = manager.retrieve_column_list(tbl_name=SENTENCE_TBL_NAME, condition='is_validated = true', columns=['sentence'])
        embeddings = manager.retrieve_column_list(tbl_name=SENTENCE_TBL_NAME, condition='is_validated = true', columns=['embedding'])
        reduced_embeddings = manager.retrieve_column_list(tbl_name=SENTENCE_TBL_NAME, condition='is_validated = true', columns=['reduced_embedding'])

        fig = model.visualize_documents(
            docs=np.array(docs),
            embeddings=np.vstack(embeddings).astype(np.float32),
            reduced_embeddings=np.vstack(reduced_embeddings).astype(np.float32),
            hide_annotations=True,
            hide_document_hover=True
        )
        return fig


