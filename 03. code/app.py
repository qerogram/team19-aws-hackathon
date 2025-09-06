#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import DataAgent
import os
from dotenv import load_dotenv
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

app = FastAPI(title="SQL Data Analysis Agent API", version="1.0.0")
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instance
agent = None

class QueryRequest(BaseModel):
    question: str
    provider: str = "bedrock"
    model: str = None

class QueryResponse(BaseModel):
    answer: str
    status: str = "success"

@app.on_event("startup")
async def startup_event():
    """Initialize the agent on startup"""
    global agent
    try:
        agent = DataAgent(provider="bedrock")
        print("Agent initialized successfully")
    except Exception as e:
        print(f"Failed to initialize agent: {e}")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "SQL Data Analysis Agent API is running"}

@app.get("/health")
async def health_check():
    """Health check with agent status"""
    if agent is None:
        return {"status": "error", "message": "Agent not initialized"}
    return {"status": "healthy", "message": "Agent is ready"}

@app.post("/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest):
    """Query the SQL data analysis agent"""
    start_time = time.time()
    logging.info(f"[QUERY START] Received question: {request.question[:100]}...")
    
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    try:
        logging.info(f"[AGENT CALL] Starting agent.run() at {time.time() - start_time:.2f}s")
        response = agent.run(request.question)
        
        elapsed = time.time() - start_time
        logging.info(f"[QUERY COMPLETE] Total time: {elapsed:.2f}s")
        
        return QueryResponse(
            answer=response["output"],
            status="success"
        )
    except Exception as e:
        elapsed = time.time() - start_time
        logging.error(f"[QUERY ERROR] Error after {elapsed:.2f}s: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

@app.post("/reinitialize")
async def reinitialize_agent(provider: str = "bedrock", model: str = None):
    """Reinitialize agent with different provider/model"""
    global agent
    try:
        agent = DataAgent(provider=provider, model=model)
        return {"status": "success", "message": f"Agent reinitialized with {provider}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reinitialization failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
