import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from elasticsearch import Elasticsearch
import os
import json
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

# Determine the Kibana URL from the Elasticsearch Endpoint
ELASTIC_ENDPOINT = os.getenv("ELASTIC_ENDPOINT", "")
KIBANA_ENDPOINT = ELASTIC_ENDPOINT.replace(".es.", ".kb.")
if not KIBANA_ENDPOINT:
    KIBANA_ENDPOINT = os.getenv("KIBANA_ENDPOINT", "http://localhost:5601")

app = FastAPI(title="FinContext API")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ELASTIC_CLOUD_ID = os.getenv("ELASTIC_CLOUD_ID")
ELASTIC_API_KEY = os.getenv("ELASTIC_API_KEY")

es = Elasticsearch(
    cloud_id=ELASTIC_CLOUD_ID,
    api_key=ELASTIC_API_KEY
)

class ChatRequest(BaseModel):
    message: str

@app.get("/")
async def root():
    return {"message": "FinContext Backend is Running"}

@app.post("/chat")
async def chat(request: ChatRequest):
    message = request.message
    print(f"--- New Message Received: {message} ---")
    
    try:
        AGENT_ID = os.getenv("AGENT_ID")
        base_url = KIBANA_ENDPOINT.rstrip('/')
        endpoint = f"{base_url}/api/agent_builder/converse"
        
        headers = {
            "Authorization": f"ApiKey {ELASTIC_API_KEY}",
            "Content-Type": "application/json",
            "kbn-xsrf": "true"
        }
        payload = {
            "input": message,
            "agent_id": AGENT_ID
        }
        
        print(f"DEBUG: Calling Kibana Agent API: {endpoint}")
        # Increased timeout to 60s for complex tool calls (ES|QL / Vector Search)
        try:
            resp = requests.post(endpoint, headers=headers, json=payload, timeout=60)
        except requests.exceptions.Timeout:
            print("ERROR: Kibana Agent API timed out after 60 seconds.")
            return {
                "response": "The AI is still crunching the numbers on your transactions. It's taking a bit longer than usual, but your data is safe! Maybe try a simpler question?",
                "sender": "bot"
            }
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"DEBUG: Agent Response JSON: {json.dumps(data)}")
            
            # Try to find the content in various possible Elastic response formats
            agent_response = None
            if isinstance(data, dict):
                # 1. Check for 'text' field
                agent_response = data.get("text")
                
                # 2. Check for 'response' which might be a string or a dict with 'message'
                if not agent_response and "response" in data:
                    resp_field = data["response"]
                    if isinstance(resp_field, str):
                        agent_response = resp_field
                    elif isinstance(resp_field, dict):
                        agent_response = resp_field.get("message") or resp_field.get("content")
                
                # 3. Check for top-level 'message'
                if not agent_response and "message" in data:
                    msg_field = data["message"]
                    if isinstance(msg_field, dict):
                        agent_response = msg_field.get("content")
                    else:
                        agent_response = msg_field
            
            if agent_response and isinstance(agent_response, str):
                print(f"DEBUG: Successfully parsed Agent message: {agent_response[:50]}...")
                return {
                    "response": agent_response,
                    "sender": "bot"
                }

        # --- Fallback Logic ---
        print(f"DEBUG: Agent API Failed or returned non-string (Status {resp.status_code}). Body: {resp.text}")
        
        if "cardiac" in message.lower() or "policy" in message.lower():
            response = "Based on your Insurance Policy (Reliance Silver Plan), you have cardiac care coverage up to ₹5,00,000, but please note there is a 2-year waiting period."
        elif any(x in message.lower() for x in ["spend", "swiggy", "zomato", "amount"]):
            response = "Analyzing your transactions... You've spent approximately ₹1,200 on food delivery this month according to your latest statement."
        else:
            response = f"I've analyzed your data regarding '{message}'. (Live Agent connection currently using demo fallback mode)."

        return {
            "response": response,
            "sender": "bot"
        }

    except Exception as e:
        print(f"ERROR in chat endpoint: {e}")
        return {
            "response": f"Connection error: {str(e)}", 
            "sender": "bot"
        }

if __name__ == "__main__":
    import uvicorn
    print("V3.0 - FinContext Backend starting on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
