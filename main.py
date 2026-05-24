from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
import requests
import json
import os
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Vercel + FastAPI",
    description="Vercel + FastAPI",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SHOP = os.getenv("SHOPIFY_SHOP")
CLIENT_ID = os.getenv("SHOPIFY_CLIENT_ID")
TOKEN = os.getenv("SHOPIFY_TOKEN")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

@app.get("/api/test")
def test_api():
    print("Testing API endpoint...")

    auth_url = f"https://{SHOP}/admin/oauth/access_token"

    json = {
        "code": "09f5436e59b93bbf453b5f7b60fc0195",
        "client_id": CLIENT_ID,
        "client_secret": TOKEN,
    }

    x = requests.post(auth_url, json=json)

    return { 
        "message": "Testing API endpoint. Check the console for details.",
        "auth_url": auth_url,
        "redirect_response": x.text
    }

@app.get("/api/data")
def get_sample_data():

    url = f"https://{SHOP}/admin/api/2026-04/graphql.json"

    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": ACCESS_TOKEN
    }

    all_edges = []
    cursor = None

    while True:

        after_clause = f', after: "{cursor}"' if cursor else ""

        query = f"""
        {{
          codeDiscountNodes(first: 250{after_clause}) {{
            pageInfo {{
              hasNextPage
              endCursor
            }}
            edges {{
              node {{
                id
                codeDiscount {{
                  ... on DiscountCodeBasic {{
                    title
                    status
                    tags
                    codes(first: 10) {{
                      nodes {{
                        code
                      }}
                    }}
                    startsAt
                    endsAt
                  }}

                  ... on DiscountCodeBxgy {{
                    title
                    status
                    tags
                    codes(first: 10) {{
                      nodes {{
                        code
                      }}
                    }}
                    startsAt
                    endsAt
                  }}

                  ... on DiscountCodeFreeShipping {{
                    title
                    status
                    tags
                    codes(first: 10) {{
                      nodes {{
                        code
                      }}
                    }}
                    startsAt
                    endsAt
                  }}
                }}
              }}
            }}
          }}
        }}
        """

        response = requests.post(
            url,
            headers=headers,
            json={"query": query}
        )

        response.raise_for_status()

        data = response.json()

        result = data["data"]["codeDiscountNodes"]

        all_edges.extend(result["edges"])

        if not result["pageInfo"]["hasNextPage"]:
            break

        cursor = result["pageInfo"]["endCursor"]

    all_discounts = [
        edge["node"]
        for edge in all_edges
        if "all" in edge["node"]["codeDiscount"].get("tags", [])
    ]

    return {
        "count": len(all_discounts),
        "data": all_discounts
    }

@app.get("/api/items/{item_id}")
def get_item(item_id: int):
    return {
        "item": {
            "id": item_id,
            "name": "Sample Item " + str(item_id),
            "value": item_id * 100
        },
        "timestamp": "2024-01-01T00:00:00Z"
    }


@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Weex Coupon</title>
    </head>
    <body>
        Weex Coupon
    </body>
    </html>
    """