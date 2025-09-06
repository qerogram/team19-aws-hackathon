#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import argparse

class AgentAPIClient:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
    
    def health_check(self):
        """Check if the API is healthy"""
        try:
            response = requests.get(f"{self.base_url}/health")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def query(self, question, provider="bedrock", model=None):
        """Send a query to the agent"""
        payload = {
            "question": question,
            "provider": provider
        }
        if model:
            payload["model"] = model
            
        try:
            response = requests.post(f"{self.base_url}/query", json=payload)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"error": str(e)}
    
    def reinitialize(self, provider="bedrock", model=None):
        """Reinitialize the agent"""
        params = {"provider": provider}
        if model:
            params["model"] = model
            
        try:
            response = requests.post(f"{self.base_url}/reinitialize", params=params)
            return response.json()
        except Exception as e:
            return {"error": str(e)}

def main():
    parser = argparse.ArgumentParser(description="SQL Data Analysis Agent API Client")
    parser.add_argument("--url", default="http://localhost:5000", help="API base URL")
    parser.add_argument("--question", "-q", help="Question to ask the agent")
    parser.add_argument("--provider", default="bedrock", help="LLM provider")
    parser.add_argument("--model", help="Specific model to use")
    parser.add_argument("--health", action="store_true", help="Check API health")
    
    args = parser.parse_args()
    
    client = AgentAPIClient(args.url)
    
    if args.health:
        result = client.health_check()
        print(json.dumps(result, indent=2))
        return
    
    if args.question:
        result = client.query(args.question, args.provider, args.model)
        print(json.dumps(result, indent=2))
        return
    
    # Interactive mode
    print("SQL Data Analysis Agent API Client")
    print("Type 'quit' to exit, 'health' to check status")
    
    while True:
        try:
            question = input("\nEnter your question: ").strip()
            
            if question.lower() == 'quit':
                break
            elif question.lower() == 'health':
                result = client.health_check()
                print(json.dumps(result, indent=2))
            elif question:
                result = client.query(question, args.provider, args.model)
                if "error" in result:
                    print(f"Error: {result['error']}")
                else:
                    print(f"\nAnswer: {result['answer']}")
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
