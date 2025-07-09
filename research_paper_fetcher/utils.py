"""Utility functions and data models for the research paper fetcher."""

from dataclasses import dataclass
from typing import List, Optional
import re


@dataclass
class Author:
    """Represents an author with their affiliation information."""
    name: str
    affiliation: str
    email: Optional[str] = None


@dataclass
class Paper:
    """Represents a research paper with its metadata."""
    pubmed_id: str
    title: str
    publication_date: str
    authors: List[Author]
    corresponding_author_email: Optional[str] = None


@dataclass
class FilteredPaper:
    """Represents a filtered paper with non-academic authors."""
    pubmed_id: str
    title: str
    publication_date: str
    non_academic_authors: List[str]
    company_affiliations: List[str]
    corresponding_author_email: Optional[str]


class CompanyDetector:
    """Detects pharmaceutical and biotech companies in author affiliations."""
    
    PHARMA_BIOTECH_KEYWORDS = [
        'pharmaceutical', 'pharma', 'biotech', 'biotechnology', 'biopharmaceutical',
        'drug', 'therapeutics', 'medicine', 'clinical', 'research and development',
        'r&d', 'life sciences', 'biopharma'
    ]
    ACADEMIC_KEYWORDS = [
        'university', 'college', 'school', 'institute', 'department', 'faculty',
        'laboratory', 'lab', 'center', 'centre', 'hospital', 'medical center',
        'research institute', 'academy', 'foundation'
    ]
    COMPANY_NAMES = [
        "novartis", "pfizer", "roche", "astrazeneca", "gilead",
        "johnson & johnson", "lilly", "sanofi", "bayer", "abbvie",
        "bristol-myers", "amgen", "regeneron", "biogen", "merck",
        "takeda", "genentech", "boehringer", "vertex", "illumina",
        "novo nordisk", "servier"
    ]
    @classmethod
    def is_non_academic(cls, affiliation: str) -> bool:
        """Check if an affiliation is non-academic."""

        print(f"DEBUG affiliation check: {affiliation}")

        affiliation_lower = affiliation.lower()

        # Check for known company names first
        for company in cls.COMPANY_NAMES:
            if company in affiliation_lower:
                # print(f"Matched known company: {company} in {affiliation}")
                return True

        # Check for corporate suffixes
        corporate_patterns = [
            r'\binc\.?\b', r'\bcorp\.?\b', r'\bltd\.?\b', r'\bllc\.?\b',
            r'\bco\.?\b', r'\bcompany\b', r'\bcorporation\b'
        ]

        for pattern in corporate_patterns:
            if re.search(pattern, affiliation_lower):
                # print(f"Matched corporate pattern: {pattern} in {affiliation}")
                return True

        # Check for academic keywords
        for keyword in cls.ACADEMIC_KEYWORDS:
            if keyword in affiliation_lower:
                # print(f"Academic keyword detected: {keyword} in {affiliation}")
                return False

        # Check for pharma/biotech keywords
        for keyword in cls.PHARMA_BIOTECH_KEYWORDS:
            if keyword in affiliation_lower:
                # print(f"Matched pharma/biotech keyword: {keyword} in {affiliation}")
                return True

        return False

    @classmethod
    def extract_company_name(cls, affiliation: str) -> str:
        """Extract company name from affiliation string."""
        # Simple extraction - take the first part before comma or semicolon
        parts = re.split(r'[,;]', affiliation)
        return parts[0].strip()