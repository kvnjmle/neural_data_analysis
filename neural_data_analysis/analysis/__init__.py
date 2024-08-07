from .Electrode import Electrode
from .Event import Event
from .embedder_utils import embedder_config, embedder_from_spec, create_image_embeddings
from .ImageEmbedder import (
    CLIPEmbedder,
    ResNet50Embedder,
    ImageEmbedder,
    DINOEmbedder,
)

from .LinearModelWrapper import LinearModelWrapper
from .model_evaluation import (
    append_model_scores,
    evaluate_model_performance,
    calculate_model_performance,
    average_across_iterations,
)
from .Neuron import Neuron
from .population import dataframe_from_cells, subset_cells, brain_area_dict
from .single_neuron import calc_firing_rates

from .MLPModel import (
    MLPModelWrapper,
)
from .stats import t_test
from .TextEmbedder import SGPTEmbedder, TextEmbedder
from .text_processing import (
    get_synonyms_wordnet,
    get_stem,
    create_word_groups,
    reduce_word_list_synonyms,
    create_excluded_words,
)

__version__ = "0.0.1"
__description__ = "A package for the data analysis pipeline of data validation, data wrangling, and hypothesis testing."
__all__ = [f for f in dir() if not f.startswith("_")]
