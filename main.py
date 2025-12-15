"""
Main Application Entry Point
Demonstrates usage of the Confluence Gen AI Agent
"""

import os
import sys
from dotenv import load_dotenv
from genai_agent import ConfluenceGenAIAgent

load_dotenv()


def main():
    """Main application function"""
    print("=" * 60)
    print("Confluence Gen AI Agent")
    print("=" * 60)
    print()
    
    try:
        # Initialize the agent
        print("Initializing Confluence connection and Gen AI agent...")
        agent = ConfluenceGenAIAgent()
        print("✓ Connected successfully!\n")
        
        # Example 1: Get available spaces
        print("Example 1: Getting available Confluence spaces...")
        print("-" * 60)
        spaces = agent.get_available_spaces()
        if spaces:
            for space in spaces[:5]:  # Show first 5
                print(f"  • {space['name']} (Key: {space['key']})")
        print()
        
        # Example 2: Interactive query mode
        print("=" * 60)
        print("Interactive Query Mode")
        print("You can now ask questions about your Confluence data.")
        print("Type 'exit' to quit, 'spaces' to see all spaces")
        print("=" * 60)
        print()
        
        while True:
            try:
                user_input = input("Ask a question about Confluence: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("\nGoodbye!")
                    break
                
                if user_input.lower() == 'spaces':
                    spaces = agent.get_available_spaces()
                    print("\nAvailable Spaces:")
                    for space in spaces:
                        print(f"  • {space['name']} (Key: {space['key']})")
                    print()
                    continue
                
                # Process the query
                print("\nProcessing your query...")
                response = agent.query(user_input)
                print("\n" + "=" * 60)
                print("Response:")
                print("=" * 60)
                print(response)
                print()
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {str(e)}\n")
                continue
    
    except ValueError as e:
        print(f"Configuration Error: {str(e)}")
        print("\nPlease make sure you have:")
        print("1. Created a .env file based on env_template.txt")
        print("2. Filled in all required credentials")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
