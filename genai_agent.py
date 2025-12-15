"""
Gen AI Agent Module
Uses OpenAI to create an intelligent agent that queries Confluence data
"""

import os
from typing import List, Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv
import logging

from confluence_connector import ConfluenceConnector

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceGenAIAgent:
    """Gen AI Agent that intelligently queries Confluence data"""
    
    def __init__(self):
        """Initialize the Gen AI agent"""
        api_key = os.getenv("OPENAI_API_KEY")
        # Default to gpt-3.5-turbo which is more widely available
        # Users can override with OPENAI_MODEL env variable
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=api_key)
        self.confluence = ConfluenceConnector()
        self.confluence.connect()
    
    def _format_search_results(self, results: List[Dict]) -> str:
        """Format search results for the AI model"""
        if not results:
            return "No results found."
        
        formatted = "Search Results:\n"
        for i, result in enumerate(results, 1):
            formatted += f"\n{i}. Title: {result.get('title', 'N/A')}\n"
            formatted += f"   Space: {result.get('space_name', result.get('space', 'N/A'))}\n"
            formatted += f"   Type: {result.get('type', 'N/A')}\n"
            if result.get('content'):
                formatted += f"   Content: {result.get('content', '')[:200]}...\n"
            if result.get('url'):
                formatted += f"   URL: {result.get('url', 'N/A')}\n"
        
        return formatted
    
    def _format_pages(self, pages: List[Dict], space_key: str) -> str:
        """Format pages for the AI model"""
        if not pages:
            return f"No pages found in space: {space_key}"
        
        formatted = f"Pages from space '{space_key}':\n"
        for i, page in enumerate(pages, 1):
            formatted += f"\n{i}. {page.get('title', 'N/A')}\n"
            formatted += f"   ID: {page.get('id', 'N/A')}\n"
            if page.get('content'):
                formatted += f"   Preview: {page.get('content', '')[:150]}...\n"
            if page.get('url'):
                formatted += f"   URL: {page.get('url', 'N/A')}\n"
        
        return formatted
    
    def _format_spaces(self, spaces: List[Dict]) -> str:
        """Format spaces for the AI model"""
        if not spaces:
            return "No spaces found."
        
        formatted = "Available Confluence Spaces:\n"
        for i, space in enumerate(spaces, 1):
            formatted += f"\n{i}. {space.get('name', 'N/A')} (Key: {space.get('key', 'N/A')})\n"
            if space.get('description'):
                formatted += f"   Description: {space.get('description', '')[:100]}...\n"
            formatted += f"   Type: {space.get('type', 'N/A')}\n"
        
        return formatted
    
    def query(self, user_query: str) -> str:
        """
        Main method to query Confluence using Gen AI
        
        The agent will:
        1. Analyze the user query
        2. Determine what Confluence data is needed
        3. Fetch the data
        4. Process and summarize using AI
        """
        try:
            # Step 1: Use AI to understand the query and determine actions
            system_prompt = """You are an intelligent Confluence assistant. 
            When a user asks a question, analyze it and determine:
            1. Whether they want to search for something specific
            2. Whether they want to see spaces
            3. Whether they want to see pages from a specific space
            4. What keywords or space names are relevant
            
            Respond ONLY with a JSON object containing:
            {
                "action": "search" | "get_pages" | "get_spaces" | "general",
                "space_key": "key of space if applicable",
                "search_query": "search keywords if applicable",
                "max_results": number
            }"""
            
            analysis_response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                temperature=0.1
            )
            
            import json
            analysis = json.loads(analysis_response.choices[0].message.content)
            
            # Step 2: Fetch data from Confluence based on analysis
            confluence_data = ""
            action = analysis.get("action", "general")
            
            if action == "get_spaces":
                spaces = self.confluence.get_spaces(limit=analysis.get("max_results", 100))
                confluence_data = self._format_spaces(spaces)
            
            elif action == "get_pages":
                space_key = analysis.get("space_key", self.confluence.default_space)
                if space_key:
                    pages = self.confluence.get_pages_from_space(
                        space_key=space_key,
                        limit=analysis.get("max_results", 50)
                    )
                    confluence_data = self._format_pages(pages, space_key)
                else:
                    confluence_data = "Space key not specified. Available spaces:\n"
                    spaces = self.confluence.get_spaces()
                    for space in spaces:
                        confluence_data += f"- {space['name']} (Key: {space['key']})\n"
            
            elif action == "search":
                search_query = analysis.get("search_query", user_query)
                space_key = analysis.get("space_key")
                results = self.confluence.search_content(
                    query=search_query,
                    space_key=space_key,
                    max_results=analysis.get("max_results", 20)
                )
                confluence_data = self._format_search_results(results)
            
            else:
                # General query - try search first
                results = self.confluence.search_content(user_query, max_results=20)
                confluence_data = self._format_search_results(results)
            
            # Step 3: Use AI to generate a natural language response
            response_prompt = f"""Based on the following Confluence data and the user's question, 
            provide a clear, helpful answer. If the data doesn't fully answer the question, 
            indicate what information is available and suggest next steps.

            User Question: {user_query}

            Confluence Data:
            {confluence_data}

            Provide a natural, conversational response that directly addresses the user's question."""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful Confluence assistant. Provide clear, concise answers based on the data provided."},
                    {"role": "user", "content": response_prompt}
                ],
                temperature=0.7
            )
            
            answer = response.choices[0].message.content
            logger.info(f"Generated response for query: {user_query[:50]}...")
            return answer
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            error_msg = str(e)
            
            # Provide helpful messages for common errors
            if "429" in error_msg or "quota" in error_msg.lower() or "insufficient_quota" in error_msg.lower():
                return """I encountered a quota/billing issue with the OpenAI API.

This usually means:
1. Your free trial credits have been used up
2. You need to add a payment method
3. You've reached your spending limit
4. You're making requests too quickly (rate limit)

To fix this:
• Go to https://platform.openai.com/account/billing and add a payment method
• Check your usage at https://platform.openai.com/account/usage
• Increase spending limits if needed
• Wait a few minutes if it's a rate limit issue

See FIX_OPENAI_QUOTA.md for detailed instructions."""
            elif "401" in error_msg or "unauthorized" in error_msg.lower():
                return """I encountered an authentication error with the OpenAI API.

Please check:
• Your OPENAI_API_KEY in the .env file is correct
• The API key hasn't been revoked
• You're using a valid API key from https://platform.openai.com/api-keys"""
            elif "404" in error_msg or "model" in error_msg.lower():
                return f"""I encountered an error with the AI model.

Please check:
• Your OPENAI_MODEL in .env is a valid model name (e.g., gpt-3.5-turbo)
• You have access to the specified model
• See FIX_MODEL_ERROR.md for model options"""
            else:
                return f"I encountered an error while processing your query: {error_msg}"
    
    def get_available_spaces(self) -> List[Dict]:
        """Get all available spaces in Confluence"""
        return self.confluence.get_spaces()
    
    def search(self, query: str, space_key: Optional[str] = None, max_results: int = 20) -> List[Dict]:
        """Direct search in Confluence"""
        return self.confluence.search_content(query, space_key=space_key, max_results=max_results)