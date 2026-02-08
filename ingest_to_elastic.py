import os
import pandas as pd
from elasticsearch import Elasticsearch, helpers
from dotenv import load_dotenv

load_dotenv()

                           
ELASTIC_CLOUD_ID = os.getenv("ELASTIC_CLOUD_ID")
ELASTIC_API_KEY = os.getenv("ELASTIC_API_KEY")

if not ELASTIC_CLOUD_ID or not ELASTIC_API_KEY:
    print("Warning: ELASTIC_CLOUD_ID or ELASTIC_API_KEY not found in environment variables.")

es = Elasticsearch(
    cloud_id=ELASTIC_CLOUD_ID,
    api_key=ELASTIC_API_KEY
)

def ingest_structured_data(file_path, index_name):
    df = pd.read_csv(file_path)
                                          
    df['Date'] = pd.to_datetime(df['Date'])
    
    actions = [
        {
            "_index": index_name,
            "_source": record
        }
        for record in df.to_dict('records')
    ]
    
    helpers.bulk(es, actions)
    print(f"Ingested {len(actions)} transactions into {index_name}")

def ingest_unstructured_data(file_path, index_name):
    with open(file_path, 'r') as f:
        content = f.read()
    
                                                                   
                                                           
    doc = {
        "text": content,
        "filename": os.path.basename(file_path),
        "metadata": {"type": "insurance_policy"}
    }
    
    es.index(index=index_name, document=doc)
    print(f"Ingested {file_path} into {index_name}")

if __name__ == "__main__":
    if ELASTIC_CLOUD_ID and ELASTIC_API_KEY:
                                       
        ingest_structured_data("../data/structured/bank_statement.csv", "fincontext-transactions")
        
                              
        ingest_unstructured_data("../data/unstructured/health_insurance_policy.md", "fincontext-documents")
    else:
        print("Please set your Elastic Cloud credentials in a .env file.")
