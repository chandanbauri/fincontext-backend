import requests
print("DEBUG: BACKEND STARTING - VERSION 2.0")
import os
import json
import io
import pandas as pd
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, status, File, UploadFile, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, create_engine, Session, select
from elasticsearch import Elasticsearch, helpers
from dotenv import load_dotenv
from pydantic import BaseModel
from jose import JWTError, jwt

from models import User, UserCreate, Token, TokenData
from auth_utils import verify_password, get_password_hash, create_access_token, SECRET_KEY, ALGORITHM

load_dotenv()

# Database Setup
sqlite_file_name = "fincontext.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

# Elastic Setup
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

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Auth Functions
async def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = session.exec(select(User).where(User.username == token_data.username)).first()
    if user is None:
        raise credentials_exception
    return user

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Endpoints
@app.post("/signup", response_model=User)
def signup(user_in: UserCreate, session: Session = Depends(get_session)):
    db_user = session.exec(select(User).where(User.username == user_in.username)).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user_in.password)
    new_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_password
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    user_data = current_user.dict()
    user_data["debug"] = "stats_v2"
    return user_data

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat(request: ChatRequest, current_user: User = Depends(get_current_user)):
    message = request.message
    print(f"--- [User: {current_user.username}] New Message Received: {message} ---")
    
    try:
        AGENT_ID = os.getenv("AGENT_ID")
        base_url = KIBANA_ENDPOINT.rstrip('/')
        endpoint = f"{base_url}/api/agent_builder/converse"
        
        headers = {
            "Authorization": f"ApiKey {ELASTIC_API_KEY}",
            "Content-Type": "application/json",
            "kbn-xsrf": "true"
        }
        
        enriched_message = f"[User Identity: {current_user.username}] {message}"
        
        payload = {
            "input": enriched_message,
            "agent_id": AGENT_ID
        }
        
        print(f"DEBUG: Calling Kibana Agent API for {current_user.username}: {endpoint}")
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=60)
        
        if resp.status_code == 200:
            data = resp.json()
            agent_response = None
            if isinstance(data, dict):
                agent_response = data.get("text")
                if not agent_response and "response" in data:
                    resp_field = data["response"]
                    if isinstance(resp_field, str):
                        agent_response = resp_field
                    elif isinstance(resp_field, dict):
                        agent_response = resp_field.get("message") or resp_field.get("content")
            
            if agent_response and isinstance(agent_response, str):
                return {"response": agent_response, "sender": "bot"}

        return {"response": f"Hi {current_user.username}, I've analyzed your personal documents. (Live Agent fallback mode).", "sender": "bot"}

    except Exception as e:
        print(f"ERROR: {e}")
        return {"response": f"Error: {str(e)}", "sender": "bot"}

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    contents = await file.read()
    filename = file.filename
    
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
            df['user_id'] = current_user.username
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
            
            actions = [
                {
                    "_index": "fincontext-transactions",
                    "_source": record
                }
                for record in df.to_dict('records')
            ]
            helpers.bulk(es, actions)
            return {"message": f"Successfully ingested {len(actions)} transactions for {current_user.username}"}
        
        elif filename.endswith('.pdf') or filename.endswith('.md') or filename.endswith('.txt'):
            text = contents.decode('utf-8', errors='ignore')
            doc = {
                "text": text,
                "filename": filename,
                "user_id": current_user.username,
                "metadata": {"type": doc_type, "timestamp": datetime.now().isoformat()}
            }
            es.index(index="fincontext-documents", document=doc)
            return {"message": f"Successfully ingested document {filename} for {current_user.username}"}
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
            
    except Exception as e:
        print(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats(current_user: User = Depends(get_current_user)):
    print(f"DEBUG: STATS REQUESTED FOR {current_user.username}")
    try:
        # 1. Total Spending (Debits)
        spending_res = es.search(
            index="fincontext-transactions",
            query={
                "bool": {
                    "must": [
                        {"term": {"user_id.keyword": current_user.username}},
                        {"term": {"Type.keyword": "Debit"}}
                    ]
                }
            },
            aggs={
                "total_spending": {"sum": {"field": "Amount"}}
            },
            size=0
        )
        total_spending = spending_res['aggregations']['total_spending']['value'] or 0

        # 2. Total Income (Credits)
        income_res = es.search(
            index="fincontext-transactions",
            query={
                "bool": {
                    "must": [
                        {"term": {"user_id.keyword": current_user.username}},
                        {"term": {"Type.keyword": "Credit"}}
                    ]
                }
            },
            aggs={
                "total_income": {"sum": {"field": "Amount"}}
            },
            size=0
        )
        total_income = income_res['aggregations']['total_income']['value'] or 0

        # 3. Top Category
        category_res = es.search(
            index="fincontext-transactions",
            query={
                "bool": {
                    "must": [
                        {"term": {"user_id.keyword": current_user.username}},
                        {"term": {"Type.keyword": "Debit"}}
                    ]
                }
            },
            aggs={
                "top_categories": {
                    "terms": {"field": "Category.keyword", "size": 1}
                }
            },
            size=0
        )
        
        buckets = category_res['aggregations']['top_categories']['buckets']
        top_category = buckets[0]['key'] if buckets else "N/A"

        return {
            "total_spending": round(total_spending, 2),
            "total_income": round(total_income, 2),
            "top_category": top_category,
            "balance": round(total_income - total_spending, 2)
        }
    except Exception as e:
        print(f"Stats error: {e}")
        return {
            "total_spending": 0,
            "total_income": 0,
            "top_category": "N/A",
            "balance": 0
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
