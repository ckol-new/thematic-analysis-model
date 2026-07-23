from .data_management import Loader, Manager
from .dataclasses import TrialConfig, ValidationMetric, ModelOutput
from thematic_analysis_model.view.visualizing import Visualizer

from bertopic import BERTopic

# validation of models
class Validator:
    def __init__(self, model: BERTopic, loader: Loader, manager: Manager, visualizer: Visualizer, trial_config: TrialConfig | None = None):
        self.model = model
        self.model.calculate_probabilities = True
        self.loader = loader
        self.manager = manager
        self.visualizer = Visualizer
        self.trial_config = trial_config

    # main entry
    #   validates, generates validation metrics, reassigns document positions, generates visuals, serializes Model Output
    def run_validator(self) -> ModelOutput:
        # reassign document position

        # generate validation metrics

        # generate visualizations/figures

        # save model output

        return
        ...

    # reassings document position in loaded model
    #   returns reduced embedding values for later (visualize document position)
    #   serialize data to lance
    #   use transform
    def reassign_document_position(self):
        # get batch of document
        #   transform
        #   serialize data output (reduced embeddings, topic, probability data)
        ...

    # get validation metrics
    #   including NPMI score, pairwise topic coherence, intertopic cosine similarity, topic diversity, probability values, redundant pairs, stability metrics
    def get_validation_metrics(self) -> ValidationMetric:
        ...


    # gets visualizations using functions from Visualizer
    def get_visualizations(self):
        ...
    