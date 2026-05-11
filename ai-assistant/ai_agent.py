import os
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types

from pathlib import Path
load_dotenv(Path(__file__).parent / ".env")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

BACKEND_URL = "http://127.0.0.1:8000"

SYSTEM_PROMPT = """You are an AI assistant for an e-commerce management system.
You help business owners with questions about their orders, products, inventory, and daily operations.
When asked about orders, products, inventory or dashboard data, use the available tools to fetch real data.
Always give short, clear answers. Maximum 3-4 sentences."""

# Araçlar - backend'den veri çeker
def get_orders():
    response = httpx.get(f"{BACKEND_URL}/orders")
    return response.json()

def get_products():
    response = httpx.get(f"{BACKEND_URL}/products")
    return response.json()

def get_inventory():
    response = httpx.get(f"{BACKEND_URL}/inventory")
    return response.json()

def get_dashboard():
    response = httpx.get(f"{BACKEND_URL}/dashboard")
    return response.json()

# Gemini'ye tanıtılacak araçlar
tools = types.Tool(function_declarations=[
    types.FunctionDeclaration(
        name="get_orders",
        description="Get all orders with customer name, product, status and price",
        parameters=types.Schema(type=types.Type.OBJECT, properties={})
    ),
    types.FunctionDeclaration(
        name="get_products",
        description="Get all products with stock levels and prices",
        parameters=types.Schema(type=types.Type.OBJECT, properties={})
    ),
    types.FunctionDeclaration(
        name="get_inventory",
        description="Get inventory levels and critical stock alerts",
        parameters=types.Schema(type=types.Type.OBJECT, properties={})
    ),
    types.FunctionDeclaration(
        name="get_dashboard",
        description="Get dashboard summary: total orders, pending orders, low stock count",
        parameters=types.Schema(type=types.Type.OBJECT, properties={})
    ),
])

# Araç çağrılarını çalıştır
def run_tool(name):
    if name == "get_orders":
        return get_orders()
    elif name == "get_products":
        return get_products()
    elif name == "get_inventory":
        return get_inventory()
    elif name == "get_dashboard":
        return get_dashboard()
    return {}

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
def chat(request: ChatRequest):
    # İlk Gemini çağrısı
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=request.message,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[tools]
        )
    )

    # Function calling var mı kontrol et
    for part in response.candidates[0].content.parts:
        if part.function_call:
            tool_name = part.function_call.name
            tool_result = run_tool(tool_name)

            # Sonucu Gemini'ye geri yolla
            final_response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=[
                    types.Content(role="user", parts=[types.Part(text=request.message)]),
                    types.Content(role="model", parts=[part]),
                    types.Content(role="user", parts=[
                        types.Part(
                            function_response=types.FunctionResponse(
                                name=tool_name,
                                response={"result": str(tool_result)}
                            )
                        )
                    ])
                ],
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT
                )
            )
            return {"answer": final_response.text}

    return {"answer": response.text}