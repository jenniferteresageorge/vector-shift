from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from integrations.airtable import authorize_airtable, get_items_airtable, oauth2callback_airtable, get_airtable_credentials
from integrations.notion import authorize_notion, get_items_notion, oauth2callback_notion, get_notion_credentials
from integrations.hubspot import authorize_hubspot, get_hubspot_credentials, get_items_hubspot, oauth2callback_hubspot
import json
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis
import httpx

app = FastAPI()

origins = [
    "http://localhost:3000",  # React app address
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class HubSpotAuthRequest(BaseModel):
    user_id: str
    org_id: str
    
class HubSpotCredentialsRequest(BaseModel):
    user_id: str
    org_id: str
    

@app.get('/')
def read_root():
    return {'Ping': 'Pong'}


# Airtable
@app.post('/integrations/airtable/authorize')
async def authorize_airtable_integration(user_id: str = Form(...), org_id: str = Form(...)):
    return await authorize_airtable(user_id, org_id)

@app.get('/integrations/airtable/oauth2callback')
async def oauth2callback_airtable_integration(request: Request):
    return await oauth2callback_airtable(request)

@app.post('/integrations/airtable/credentials')
async def get_airtable_credentials_integration(user_id: str = Form(...), org_id: str = Form(...)):
    return await get_airtable_credentials(user_id, org_id)

@app.post('/integrations/airtable/load')
async def get_airtable_items(credentials: str = Form(...)):
    return await get_items_airtable(credentials)


# Notion
@app.post('/integrations/notion/authorize')
async def authorize_notion_integration(user_id: str = Form(...), org_id: str = Form(...)):
    return await authorize_notion(user_id, org_id)

@app.get('/integrations/notion/oauth2callback')
async def oauth2callback_notion_integration(request: Request):
    return await oauth2callback_notion(request)

@app.post('/integrations/notion/credentials')
async def get_notion_credentials_integration(user_id: str = Form(...), org_id: str = Form(...)):
    return await get_notion_credentials(user_id, org_id)

@app.post('/integrations/notion/load')
async def get_notion_items(credentials: str = Form(...)):
    return await get_items_notion(credentials)

# HubSpot
@app.post('/integrations/hubspot/authorize')
async def authorize_hubspot_api(request: HubSpotAuthRequest):
    auth_url = await authorize_hubspot(request.user_id, request.org_id)
    return {"auth_url": auth_url}
@app.get('/integrations/hubspot/oauth2callback')
async def oauth2callback_hubspot_integration(request: Request):
    return await oauth2callback_hubspot(request)

@app.post("/integrations/hubspot/credentials")
async def get_hubspot_credentials_api(request: HubSpotCredentialsRequest):
    credentials = await get_value_redis(f"hubspot_credentials:{request.org_id}:{request.user_id}")

    if not credentials:
        raise HTTPException(status_code=400, detail="❌ No credentials found in Redis.")

    if isinstance(credentials, bytes):
        credentials = credentials.decode("utf-8")  # Convert Redis byte response to string

    return json.loads(credentials)

@app.post('/integrations/hubspot/get_hubspot_items')
async def load_slack_data_integration():
    return await get_items_hubspot()
