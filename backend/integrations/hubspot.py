import json
import secrets
import base64
import hashlib
import httpx
import asyncio
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
from integrations.integration_item import IntegrationItem
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis
from datetime import datetime
CLIENT_ID = "5121a21e-7523-4533-b72b-c7df05b6205a"
CLIENT_SECRET = "2ab5036e-4942-400f-ba41-e8b78cd9704d"
REDIRECT_URI = "http://localhost:8000/integrations/hubspot/oauth2callback"
AUTHORIZATION_URL = "https://app.hubspot.com/oauth/authorize"
TOKEN_URL = "https://api.hubapi.com/oauth/v1/token"
SCOPE = "crm.objects.contacts.read"  # Adjust scope as needed

def generate_state_verifier():
    state = secrets.token_urlsafe(32)
    code_verifier = secrets.token_urlsafe(32)
    m = hashlib.sha256()
    m.update(code_verifier.encode("utf-8"))
    code_challenge = base64.urlsafe_b64encode(m.digest()).decode("utf-8").replace("=", "")
    return state, code_verifier, code_challenge

async def authorize_hubspot(user_id, org_id):
    state, code_verifier, code_challenge = generate_state_verifier()
    auth_url = f"{AUTHORIZATION_URL}?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}" \
               f"&scope={SCOPE}&response_type=code&state={state}&code_challenge={code_challenge}&code_challenge_method=S256"

    redis_key_state = f"hubspot_state:{org_id}:{user_id}"
    redis_key_verifier = f"hubspot_verifier:{org_id}:{user_id}"

    # Store in Redis and capture return values
    state_result = await add_key_value_redis(redis_key_state, state, expire=1200)
    verifier_result = await add_key_value_redis(redis_key_verifier, code_verifier, expire=1200)

    print("✅ Redis SET Result for State:", state_result)
    print("✅ Redis SET Result for Code Verifier:", verifier_result)
    print("✅ Corrected Redis Key for State:", redis_key_state)
    print("✅ Corrected Redis Key for Code Verifier:", redis_key_verifier)
    print("✅ Saved Code Verifier in Redis:", code_verifier)

    return auth_url

async def oauth2callback_hubspot(request: Request):

    code = request.query_params.get("code")
    state = request.query_params.get("state")



    user_id, org_id = "test_user", "test_org"

    saved_state, code_verifier = await asyncio.gather(
        get_value_redis(f"hubspot_state:{org_id}:{user_id}"),
        get_value_redis(f"hubspot_verifier:{org_id}:{user_id}")
    )

    print("🔹 Retrieved State from Redis:", saved_state if saved_state else None)
    print("🔹 Retrieved Code Verifier from Redis:", code_verifier if code_verifier else None)

    if not saved_state or not code_verifier:
        raise HTTPException(status_code=400, detail="❌ Missing 'state' or 'code_verifier' in Redis. Try re-authorizing.")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.hubapi.com/oauth/v1/token",
            data={
                "grant_type": "authorization_code",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
                "code": code,
                "code_verifier": code_verifier,
            },
        )

    print("Token Response Status:", response.status_code)
    print("Token Response JSON:", response.json())

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to exchange token.")

    token_data = response.json()
    await add_key_value_redis(f"hubspot_credentials:{org_id}:{user_id}", json.dumps(token_data), expire=3600)

    return HTMLResponse("<html><script>window.close();</script></html>")


async def get_hubspot_credentials(user_id, org_id):
    credentials = await get_value_redis(f"hubspot_credentials:{org_id}:{user_id}")
    if not credentials:
        raise HTTPException(status_code=400, detail="No credentials found.")
    return json.loads(credentials)

def parse_hubspot_datetime(iso_str):
    """Convert HubSpot ISO date string to Python datetime object."""
    if not iso_str:
        return None  # Handle missing dates gracefully
    return datetime.strptime(iso_str.replace("Z", ""), "%Y-%m-%dT%H:%M:%S.%f")

async def get_items_hubspot(user_id: str = "test_user", org_id: str = "test_org"):
    # ✅ Fetch OAuth credentials from Redis
    stored_credentials = await get_value_redis(f"hubspot_credentials:{org_id}:{user_id}")

    if not stored_credentials:
        raise HTTPException(status_code=400, detail="❌ No HubSpot credentials found in Redis. Please reauthorize.")

    # ✅ Decode credentials from Redis
    if isinstance(stored_credentials, bytes):
        stored_credentials = stored_credentials.decode("utf-8")

    try:
        credentials = json.loads(stored_credentials)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="❌ Invalid credentials format. Try reauthorizing.")

    access_token = credentials.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="❌ Missing access token in stored credentials.")

    print(f"🔹 Using Access Token: {access_token[:10]}... (masked for security)")

    # ✅ Query HubSpot Contacts API
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    url = "https://api.hubapi.com/crm/v3/objects/contacts"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail=f"❌ Failed to fetch HubSpot contacts: {response.text}")

    hubspot_data = response.json().get("results", [])

    # ✅ Convert API response to a list of IntegrationItem objects
    integration_items = []
    
    for item in hubspot_data:
        properties = item.get("properties", {})
        
        integration_item = IntegrationItem(
            id=item.get("id"),
            type="HubSpot Contact",
            name=f"{properties.get('firstname', '')} {properties.get('lastname', '')}".strip(),
            creation_time=parse_hubspot_datetime(properties.get("createdate")),
            last_modified_time=parse_hubspot_datetime(properties.get("lastmodifieddate")),
            url=f"https://app.hubspot.com/contacts/{item.get('id')}",
            mime_type="contact",
            visibility=True
        )
        integration_items.append(integration_item)

    # ✅ Print Integration Items to Console (Backend Logging)
    print("\n✅ HubSpot Contacts (Backend Log):")
    for item in integration_items:
        print(vars(item))  # Print object properties as a dictionary

    return integration_items