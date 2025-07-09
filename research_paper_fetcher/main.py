"""Main command-line interface for the research paper fetcher."""

import click
import logging
from typing import Optional

from .paper_fetcher import PubMedClient, PubMedAPIError
from .data_processor import PaperProcessor


def setup_logging(debug: bool) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


@click.command()
@click.argument('query', type=str)
@click.option('-h', '--help', is_flag=True, help='Show this help message and exit.')
@click.option('-d', '--debug', is_flag=True, help='Print debug information during execution.')
@click.option('-f', '--file', 'filename', type=str, help='Specify filename to save results.')
@click.option('--max-results', type=int, default=100, help='Maximum number of papers to fetch.')
@click.option('--email', type=str, help='Email for PubMed API (recommended).')
@click.option('--api-key', type=str, help='API key for PubMed (for higher rate limits).')
def main(query: str, help: bool, debug: bool, filename: Optional[str], 
         max_results: int, email: Optional[str], api_key: Optional[str]) -> None:
    """
    Fetch research papers from PubMed and identify papers with pharmaceutical/biotech company authors.
    
    QUERY: Search query using PubMed syntax (e.g., "cancer treatment[Title/Abstract]")
    
    Examples:
        get-papers-list "cancer treatment"
        get-papers-list "diabetes[MeSH Terms]" --file results.csv
        get-papers-list "immunotherapy" --debug --max-results 50
    """
    if help:
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        return
    
    setup_logging(debug)
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize components
        client = PubMedClient(email=email, api_key=api_key)
        processor = PaperProcessor()
        
        logger.info(f"Searching for papers with query: {query}")
        
        # Search for papers
        pubmed_ids = client.search_papers(query, max_results=max_results)
        logger.info(f"Found {len(pubmed_ids)} papers")
        
        if not pubmed_ids:
            click.echo("No papers found for the given query.")
            return
        
        # Fetch paper details
        logger.info("Fetching paper details...")
        papers = client.fetch_paper_details(pubmed_ids)
        logger.info(f"Successfully fetched details for {len(papers)} papers")
        
        # Filter papers with company authors
        logger.info("Filtering papers with pharmaceutical/biotech company authors...")
        filtered_papers = processor.filter_papers_with_company_authors(papers)
        logger.info(f"Found {len(filtered_papers)} papers with company authors")
        
        # Output results
        if filename:
            processor.save_to_csv(filtered_papers, filename)
            click.echo(f"Results saved to {filename}")
        else:
            processor.print_results(filtered_papers)
    
    except PubMedAPIError as e:
        logger.error(f"PubMed API error: {e}")
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if debug:
            raise
        click.echo(f"Unexpected error: {e}", err=True)
        raise click.Abort()


if __name__ == '__main__':
    main()