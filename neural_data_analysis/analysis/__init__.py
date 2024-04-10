from .Electrode import Electrode
from .Event import Event
from .embedder_utils import embedder_config, embedder_from_spec, create_image_embeddings
from .ImageEmbedder import (
    CLIPEmbedder,
    ResNet50Embedder,
    ImageEmbedder,
    DINOEmbedder,
)

from .LinearModel import LinearModel
from .model_evaluation import (
    append_model_scores,
    evaluate_model_performance,
    process_results_multiple_regression,
)
from .Neuron import Neuron
from .population import dataframe_from_cells, subset_cells
from .single_neuron import calc_firing_rates

from .MLPModel import (
    MLPModel,
    MLPMultiClassClassifier,
    MLPBinaryClassifier,
    MLPRegressor,
)
from .TextEmbedder import SGPTEmbedder, TextEmbedder

__version__ = "0.0.1"
__description__ = "A package for the data analysis pipeline of data validation, data wrangling, and hypothesis testing."
__all__ = [f for f in dir() if not f.startswith("_")]
