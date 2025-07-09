"""Research paper fetcher package."""

__version__ = "0.1.0"
__author__ = "Suryakant"
__email__ = "suryakant4803@gmail.com"

from .paper_fetcher import PubMedClient, PubMedAPIError
from .data_processor import PaperProcessor
from .utils import Paper, Author, FilteredPaper, CompanyDetector

__all__ = [
    'PubMedClient',
    'PubMedAPIError', 
    'PaperProcessor',
    'Paper',
    'Author',
    'FilteredPaper',
    'CompanyDetector'
]