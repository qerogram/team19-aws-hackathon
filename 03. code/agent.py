from langchain.agents import create_react_agent, AgentExecutor
from langchain.callbacks.base import BaseCallbackHandler
from tools import get_tools
from prompts import get_react_prompt
from providers import LLMProvider
import os
from dotenv import load_dotenv
import time
import logging

load_dotenv()

class ThrottleCallbackHandler(BaseCallbackHandler):
    """Callback handler that adds delay between LLM calls to prevent throttling"""
    def __init__(self, delay_seconds=2.0):
        self.delay_seconds = delay_seconds
        self.last_call_time = 0
        
    def on_llm_start(self, serialized, prompts, **kwargs):
        """Called when LLM starts generating a response"""
        current_time = time.time()
        time_since_last = current_time - self.last_call_time
        
        # Calculate how much more time we need to wait
        wait_time = max(0, self.delay_seconds - time_since_last)
        
        if wait_time > 0:
            logging.info(f"[THROTTLE] Sleeping for {wait_time:.2f}s before LLM call (ensuring {self.delay_seconds}s gap)")
            time.sleep(wait_time)
        else:
            logging.info(f"[THROTTLE] No delay needed, {time_since_last:.2f}s since last call")
    
    def on_llm_end(self, response, **kwargs):
        """Called when LLM completes generating a response"""
        # Add delay after LLM response completes for more stability
        logging.info(f"[THROTTLE] LLM response completed, adding {self.delay_seconds}s delay after response")
        time.sleep(self.delay_seconds)
        self.last_call_time = time.time()

class DataAgent:
    def __init__(self, provider="openai", model=None):
        logging.info(f"[AGENT INIT] Initializing DataAgent with provider: {provider}, model: {model}")
        self.llm = self._get_llm(provider, model)
        
        # Add throttle callback to LLM itself (3s before + 3s after = 6s total)
        throttle_handler = ThrottleCallbackHandler(delay_seconds=5.0)
        if hasattr(self.llm, 'callbacks'):
            if self.llm.callbacks:
                self.llm.callbacks.append(throttle_handler)
            else:
                self.llm.callbacks = [throttle_handler]
        
        # Streaming setting removed - ChatBedrockConverse handles it internally
        self.tools = get_tools()
        self.agent = self._create_agent()
        logging.info(f"[AGENT INIT] DataAgent initialization complete")
    
    def _get_llm(self, provider, model):
        if provider == "openai":
            return LLMProvider.get_openai(model or "gpt-3.5-turbo")
        elif provider == "bedrock":
            return LLMProvider.get_bedrock(model or "us.anthropic.claude-sonnet-4-20250514-v1:0")
        elif provider == "anthropic":
            return LLMProvider.get_anthropic(model or "claude-3-sonnet-20240229")
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
    def _create_agent(self):
        prompt = get_react_prompt()
        agent = create_react_agent(self.llm, self.tools, prompt)
        
        # Create throttle callback handler (3s before + 3s after = 6s total)
        throttle_handler = ThrottleCallbackHandler(delay_seconds=5.0)
        
        # Use standard AgentExecutor with callback
        return AgentExecutor(
            agent=agent, 
            tools=self.tools, 
            verbose=False,  # Disable verbose to reduce streaming calls
            callbacks=[throttle_handler],  # Add throttle callback
            handle_parsing_errors=True,
            return_intermediate_steps=False,
            max_iterations=10,  # Set max iterations to prevent infinite loops
            max_execution_time=300  # Increase timeout to 5 minutes for Bedrock
        )
    
    def run(self, query: str):
        start_time = time.time()
        logging.info(f"[AGENT RUN] Starting agent.invoke() for query: {query[:100]}...")
        
        try:
            result = self.agent.invoke({"input": query})
            elapsed = time.time() - start_time
            logging.info(f"[AGENT RUN] Agent.invoke() completed in {elapsed:.2f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logging.error(f"[AGENT RUN] Error after {elapsed:.2f}s: {str(e)}")
            raise
