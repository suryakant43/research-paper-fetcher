"""PubMed API client for fetching research papers."""

import requests
import xml.etree.ElementTree as ET
from typing import List, Optional, Dict, Any
import logging
from urllib.parse import urlencode
import time

from .utils import Paper, Author


class PubMedAPIError(Exception):
    """Exception raised for PubMed API errors."""
    pass


class PubMedClient:
    """Client for interacting with PubMed API."""
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    def __init__(self, email: Optional[str] = None, api_key: Optional[str] = None):
        """Initialize PubMed client."""
        self.email = email
        self.api_key = api_key
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> requests.Response:
        """Make a request to PubMed API with rate limiting."""
        if self.email:
            params['email'] = self.email
        if self.api_key:
            params['api_key'] = self.api_key
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            # Rate limiting: 3 requests per second without API key, 10 with key
            sleep_time = 0.1 if self.api_key else 0.34
            time.sleep(sleep_time)
            
            return response
        except requests.RequestException as e:
            raise PubMedAPIError(f"API request failed: {e}")
    
    def search_papers(self, query: str, max_results: int = 100) -> List[str]:
        """Search for papers and return list of PubMed IDs."""
        params = {
            'db': 'pubmed',
            'term': query,
            'retmode': 'xml',
            'retmax': max_results
        }
        
        response = self._make_request('esearch.fcgi', params)
        
        try:
            root = ET.fromstring(response.content)
            id_elements = root.findall('.//Id')
            return [id_elem.text for id_elem in id_elements if id_elem.text]
        except ET.ParseError as e:
            raise PubMedAPIError(f"Failed to parse search response: {e}")
    
    def fetch_paper_details(self, pubmed_ids: List[str]) -> List[Paper]:
        """Fetch detailed information for given PubMed IDs."""
        if not pubmed_ids:
            return []
        
        params = {
            'db': 'pubmed',
            'id': ','.join(pubmed_ids),
            'retmode': 'xml'
        }
        
        response = self._make_request('efetch.fcgi', params)
        
        try:
            root = ET.fromstring(response.content)
            papers = []
            
            for article in root.findall('.//PubmedArticle'):
                paper = self._parse_article(article)
                if paper:
                    papers.append(paper)
            
            return papers
        except ET.ParseError as e:
            raise PubMedAPIError(f"Failed to parse fetch response: {e}")
    
    def _parse_article(self, article: ET.Element) -> Optional[Paper]:
        """Parse a single article from XML."""
        try:
            # Extract PubMed ID
            pubmed_id_elem = article.find('.//PMID')
            if pubmed_id_elem is None:
                return None
            pubmed_id = pubmed_id_elem.text
            
            # Extract title
            title_elem = article.find('.//ArticleTitle')
            title = title_elem.text if title_elem is not None else "Unknown Title"
            
            # Extract publication date
            pub_date = self._extract_publication_date(article)
            
            # Extract authors
            authors = self._extract_authors(article)
            
            # Extract corresponding author email
            corresponding_email = self._extract_corresponding_email(article)
            
            return Paper(
                pubmed_id=pubmed_id,
                title=title,
                publication_date=pub_date,
                authors=authors,
                corresponding_author_email=corresponding_email
            )
        except Exception as e:
            self.logger.warning(f"Failed to parse article: {e}")
            return None
    
    def _extract_publication_date(self, article: ET.Element) -> str:
        """Extract publication date from article."""
        # Try different date fields
        date_fields = [
            './/PubDate',
            './/ArticleDate',
            './/DateCompleted'
        ]
        
        for field in date_fields:
            date_elem = article.find(field)
            if date_elem is not None:
                year = date_elem.find('Year')
                month = date_elem.find('Month')
                day = date_elem.find('Day')
                
                if year is not None:
                    date_parts = [year.text]
                    if month is not None:
                        date_parts.append(month.text.zfill(2))
                    if day is not None:
                        date_parts.append(day.text.zfill(2))
                    return '-'.join(date_parts)
        
        return "Unknown Date"
    
    def _extract_authors(self, article: ET.Element) -> List[Author]:
        """Extract authors from article."""
        authors = []
        
        for author_elem in article.findall('.//Author'):
            # Extract name
            last_name = author_elem.find('LastName')
            first_name = author_elem.find('ForeName')
            
            if last_name is not None:
                name = last_name.text
                if first_name is not None:
                    name = f"{first_name.text} {name}"
            else:
                continue
            
            # Extract affiliation
            affiliation_elem = author_elem.find('.//Affiliation')
            affiliation = affiliation_elem.text if affiliation_elem is not None else ""
            
            authors.append(Author(name=name, affiliation=affiliation))
        
        return authors
    
    def _extract_corresponding_email(self, article: ET.Element) -> Optional[str]:
        """Extract corresponding author email."""
        # Look for email in author information
        for author_elem in article.findall('.//Author'):
            affiliation_elem = author_elem.find('.//Affiliation')
            if affiliation_elem is not None:
                affiliation_text = affiliation_elem.text
                if affiliation_text:
                    # Simple email extraction
                    import re
                    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                    emails = re.findall(email_pattern, affiliation_text)
                    if emails:
                        return emails[0]
        
        return None