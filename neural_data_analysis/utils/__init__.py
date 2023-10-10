from .string_processing import get_brain_area_abbreviation, remove_lateralization
from .utils import correct_filepath, create_order_index, recursive_dict_update

__version__ = "0.0.1"
__description__ = "A package for miscellaneous functions."
__all__ = [f for f in dir() if not f.startswith("_")]
