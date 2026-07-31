from .config import *
import keras

class FrozenParametricUMAP:
    """Wrapper that prevents BERTopic from retraining the loaded UMAP model."""
    def __init__(self, model_path: str = GLOBAL_PARAMETRIC_UMAP_ENCODER_PATH):
        self.encoder = keras.models.load_model(model_path)
        self.embedding_ = None

    def fit(self, X, y=None):
        self.embedding_ = self.transform(X)
        return self

    def transform(self, X):
        # Generates reduced embeddings using the pre-trained neural network
        embeddings = self.encoder.predict(X, batch_size=256, verbose=0)
        self.embedding_ = embeddings
        return embeddings

    def fit_transform(self, X, y=None):
        return self.transform(X)