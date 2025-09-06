import os
import logging
from botocore.config import Config
from langchain_openai import ChatOpenAI
from langchain_aws import ChatBedrock, ChatBedrockConverse
from langchain_anthropic import ChatAnthropic

class LLMProvider:
    @staticmethod
    def get_openai(model="gpt-3.5-turbo", temperature=0):
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=os.getenv("OPENAI_API_KEY")
        )
    
    @staticmethod
    def get_bedrock(model="us.anthropic.claude-sonnet-4-20250514-v1:0", temperature=0):
        logging.info(f"[LLM PROVIDER] Creating ChatBedrock client with forced non-streaming for model: {model}")
        
        # Use ChatBedrock with explicitly disabled streaming
        llm = ChatBedrock(
            model_id=model,
            region_name="us-east-1", 
            model_kwargs={"temperature": temperature, "max_tokens": 4096},
            streaming=False,  # Explicitly disable streaming
            credentials_profile_name="hackathon"
        )
        
        logging.info(f"[LLM PROVIDER] ChatBedrock client created with streaming=False")
        return llm
    
    @staticmethod
    def get_anthropic(model="claude-3-5-sonnet-20241022", temperature=0):
        return ChatAnthropic(
            model=model,
            temperature=temperature,
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
