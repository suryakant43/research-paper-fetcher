"""Data processing and filtering logic for research papers."""

import pandas as pd
from typing import List, Optional
import logging

from .utils import Paper, FilteredPaper, CompanyDetector, Author


class PaperProcessor:
    """Processes and filters research papers."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.company_detector = CompanyDetector()
    
    def filter_papers_with_company_authors(self, papers: List[Paper]) -> List[FilteredPaper]:
        """Filter papers that have at least one author from a pharma/biotech company."""
        filtered_papers = []
        
        for paper in papers:
            non_academic_authors = []
            company_affiliations = []
            
            for author in paper.authors:
                if self.company_detector.is_non_academic(author.affiliation):
                    non_academic_authors.append(author.name)
                    company_name = self.company_detector.extract_company_name(author.affiliation)
                    if company_name not in company_affiliations:
                        company_affiliations.append(company_name)
            
            # Only include papers with at least one non-academic author
            if non_academic_authors:
                filtered_paper = FilteredPaper(
                    pubmed_id=paper.pubmed_id,
                    title=paper.title,
                    publication_date=paper.publication_date,
                    non_academic_authors=non_academic_authors,
                    company_affiliations=company_affiliations,
                    corresponding_author_email=paper.corresponding_author_email
                )
                filtered_papers.append(filtered_paper)
        
        return filtered_papers
    

    
    def to_dataframe(self, filtered_papers: List[FilteredPaper]) -> pd.DataFrame:
        """Convert filtered papers to pandas DataFrame."""
        data = []

        for paper in filtered_papers:
            data.append({
                'PubmedID': paper.pubmed_id,
                'Title': paper.title,
                'Publication Date': paper.publication_date,
                'Non-academic Author(s)': ' | '.join(paper.non_academic_authors),
                'Company Affiliation(s)': ' | '.join(paper.company_affiliations),
                'Corresponding Author Email': paper.corresponding_author_email or ''
            })

        return pd.DataFrame(data)

    
    def save_to_csv(self, filtered_papers: List[FilteredPaper], filename: str) -> None:
        """Save filtered papers to CSV file in Excel-friendly format."""
        df = self.to_dataframe(filtered_papers)
        df.to_csv(
            filename,
            index=False,
            encoding='utf-8-sig',
            sep=','
        )
        self.logger.info(f"Saved {len(filtered_papers)} papers to {filename}")

    
    def print_results(self, filtered_papers: List[FilteredPaper]) -> None:
        """Print results to console."""
        if not filtered_papers:
            print("No papers found with pharmaceutical/biotech company authors.")
            return
        
        df = self.to_dataframe(filtered_papers)
        print(df.to_string(index=False))