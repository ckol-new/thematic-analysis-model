from thematic_analysis_model.model.data_management import Manager

from bertopic import BERTopic
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

    def visualize_document_map(self, model: BERTopic, docs, embeddings, reduced_embeddings) -> Figure:
        return model.visualize_documents(docs=docs, embeddings=embeddings, reduced_embeddings=reduced_embeddings, hide_annotations=True, hide_document_hover=True)


