"""
Confluence Connector Module
Handles authentication and connection to Confluence
"""

import os
from typing import List, Dict, Optional
from atlassian import Confluence
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceConnector:
    """Handles Confluence authentication and data retrieval"""
    
    def __init__(self):
        """Initialize Confluence connector with credentials from environment"""
        self.url = os.getenv("CONFLUENCE_URL")
        self.username = os.getenv("CONFLUENCE_USERNAME")
        self.api_token = os.getenv("CONFLUENCE_API_TOKEN")
        
        # Optional: space key for filtering
        self.default_space = os.getenv("CONFLUENCE_SPACE_KEY", None)
        
        if not all([self.url, self.username, self.api_token]):
            raise ValueError("Missing required Confluence credentials in environment variables")
        
        self.confluence = None
    
    def connect(self) -> Confluence:
        """Establish connection to Confluence"""
        try:
            self.confluence = Confluence(
                url=self.url,
                username=self.username,
                password=self.api_token,
                cloud=True  # Set to False if using Confluence Server/Data Center
            )
            
            # Verify connection by trying to get spaces (this validates credentials)
            # Just get one space to verify connection works
            try:
                spaces = self.confluence.get_all_spaces(start=0, limit=1)
                logger.info(f"Successfully connected to Confluence as: {self.username}")
            except Exception as verify_error:
                # If getting spaces fails, try a simple API call
                # This will raise an error if credentials are wrong
                logger.warning(f"Could not verify connection by getting spaces: {verify_error}")
                # Connection object is still created, will fail on actual use if credentials are wrong
                logger.info(f"Confluence connection initialized for: {self.username}")
            
            return self.confluence
        except Exception as e:
            logger.error(f"Failed to connect to Confluence: {str(e)}")
            raise
    
    def get_spaces(self, limit: int = 100) -> List[Dict]:
        """Get all spaces from Confluence"""
        if not self.confluence:
            self.connect()
        
        try:
            spaces = self.confluence.get_all_spaces(start=0, limit=limit, expand='description.plain')
            
            result = []
            for space in spaces.get('results', []):
                result.append({
                    "key": space.get('key'),
                    "name": space.get('name'),
                    "type": space.get('type'),
                    "description": space.get('description', {}).get('plain', {}).get('value', ''),
                    "page_count": space.get('_links', {}).get('webui', '')
                })
            
            logger.info(f"Retrieved {len(result)} spaces")
            return result
        except Exception as e:
            logger.error(f"Failed to retrieve spaces: {str(e)}")
            raise
    
    def get_pages_from_space(self, space_key: str, limit: int = 100) -> List[Dict]:
        """Get all pages from a specific space"""
        if not self.confluence:
            self.connect()
        
        try:
            pages = self.confluence.get_all_pages_from_space(
                space=space_key,
                start=0,
                limit=limit,
                expand='body.storage,version'
            )
            
            result = []
            for page in pages:
                result.append({
                    "id": page.get('id'),
                    "title": page.get('title'),
                    "space": space_key,
                    "version": page.get('version', {}).get('number', 0),
                    "content": page.get('body', {}).get('storage', {}).get('value', '')[:500],  # First 500 chars
                    "url": self.url.rstrip('/') + page.get('_links', {}).get('webui', '')
                })
            
            logger.info(f"Retrieved {len(result)} pages from space: {space_key}")
            return result
        except Exception as e:
            logger.error(f"Failed to retrieve pages from space: {str(e)}")
            raise
    
    def search_content(self, query: str, space_key: Optional[str] = None, max_results: int = 50) -> List[Dict]:
        """Search for content in Confluence"""
        if not self.confluence:
            self.connect()
        
        try:
            # Build CQL (Confluence Query Language) query
            cql_query = f"text ~ \"{query}\""
            if space_key:
                cql_query += f" AND space = {space_key}"
            
            search_results = self.confluence.cql(
                cql=cql_query,
                limit=max_results,
                expand='body.storage,version,space'
            )
            
            result = []
            for item in search_results.get('results', []):
                content = item.get('body', {}).get('storage', {}).get('value', '')
                # Remove HTML tags for cleaner text
                import re
                text_content = re.sub('<[^<]+?>', '', content)[:300]  # First 300 chars
                
                result.append({
                    "id": item.get('id'),
                    "title": item.get('title'),
                    "type": item.get('content', {}).get('type', ''),
                    "space": item.get('space', {}).get('key', ''),
                    "space_name": item.get('space', {}).get('name', ''),
                    "content": text_content,
                    "url": self.url.rstrip('/') + item.get('_links', {}).get('webui', ''),
                    "version": item.get('version', {}).get('number', 0)
                })
            
            logger.info(f"Search returned {len(result)} results for query: {query}")
            return result
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise
    
    def get_page_content(self, page_id: str) -> Optional[str]:
        """Get full content from a specific page"""
        if not self.confluence:
            self.connect()
        
        try:
            page = self.confluence.get_page_by_id(
                page_id=page_id,
                expand='body.storage,version,space'
            )
            
            if page:
                content = page.get('body', {}).get('storage', {}).get('value', '')
                # Remove HTML tags
                import re
                text_content = re.sub('<[^<]+?>', '', content)
                return text_content
            
            return None
        except Exception as e:
            logger.error(f"Failed to get page content: {str(e)}")
            return None
    
    def get_page_by_title(self, space_key: str, title: str) -> Optional[Dict]:
        """Get a page by its title in a space"""
        if not self.confluence:
            self.connect()
        
        try:
            page = self.confluence.get_page_by_title(
                space=space_key,
                title=title
            )
            
            if page:
                return {
                    "id": page.get('id'),
                    "title": page.get('title'),
                    "space": space_key,
                    "url": self.url.rstrip('/') + page.get('_links', {}).get('webui', '')
                }
            
            return None
        except Exception as e:
            logger.error(f"Failed to get page by title: {str(e)}")
            return None
