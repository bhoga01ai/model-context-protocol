# Key Benefits of the MCP Server Approach

    # No manual JSON schema writing required
    # Type hints provide automatic validation
    # Clear parameter descriptions help LLM understand tool usage
    # Error handling integrates naturally with Python exceptions
    # Tool registration happens automatically through decorators

# Key Benefits - MCP prompt soruces
    # Consistency - Users get reliable results every time
    # Expertise - You can encode domain knowledge into prompts
    # Reusability - Multiple client applications can use the same prompts
    # Maintenance - Update prompts in one place to improve all clients
    # Prompts work best when they're specialized for your MCP server's domain. A document management server might have prompts for formatting, summarizing, or analyzing documents. A data analysis server might have prompts for generating reports or visualizations.
    # The goal is to provide prompts that are so well-crafted and tested that users prefer them over writing their own instructions from scratch
# Define MCP server -- it's similar to FastAPI


# STEP 0 : Import dependencies
from dotenv import load_dotenv
load_dotenv()

import os
import yfinance as yf
import requests

weatherAPIKey = str(os.getenv('weatherAPIKey'))

# Input data for MCP TOOLS
docs = {
    "deposition.md": "This deposition covers the testimony of Angela Smith, P.E.",
    "report.pdf": "The report details the state of a 20m condenser tower.",
    "financials.docx": "These financials outline the project's budget and expenditures",
    "outlook.pdf": "This document presents the projected future performance of the system",
    "plan.md": "The plan outlines the steps for the project's implementation.",
    "spec.txt": "These specifications define the technical requirements for the equipment"
}

# STEP 1 : IMPORT FASTMCP using MCP SDK
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base
from pydantic import Field

mcp = FastMCP("DocumentMCP", log_level="ERROR")

# STEP 2 : Define MCP Tools 
# TOOL 1 : Creating a dodcument Reader tool
@mcp.tool(name="document_reader", description="Reads a document and returns its content as a string")

def document_reader(document_name: str) -> str:
    """Reads a document and returns its content as a string."""
    if document_name not in docs:
        print(f"Document {document_name} not found.")
        raise ValueError(f"Document {document_name} not found.")

    return f"Document {document_name} content: {docs[document_name]}"

# TOOL 2 : Creating a document writer tool
@mcp.tool(name="document_writer", description="Writes content to a document")
def document_writer(document_name: str, content: str) -> str:
    """Writes content to a document."""
    if document_name not in docs:
        docs[document_name] = content
        print(f"Document {document_name} not found. So created a new document.")
    else:
        docs[document_name] += content
        print(f"Document {document_name} found. So appended the content.")
    return f"Document {document_name} content: {docs[document_name]}"

# TOOL 3 : Creating a document editor tool
@mcp.tool(name="document_editor", description="Edits a document with the given content")
def document_editor(document_name: str, old_content: str, new_content: str) -> str:
    """Edits a document with the given content."""
    if document_name not in docs:
        print(f"Document {document_name} not found.")
        raise ValueError(f"Document {document_name} not found.")
    if old_content not in docs[document_name]:
        print(f"Old content not found in document {document_name}.")
        raise ValueError(f"Old content not found in document {document_name}.")
    print(f"Old content found in document {document_name}.")
    docs[document_name] = docs[document_name].replace(old_content, new_content)
    print(f"Document {document_name} content updated. New content: {docs[document_name]}")
    return f"Document {document_name} content updated. New content: {docs[document_name]}"

# TOOL 4 : Creating a number addition tool
@mcp.tool(name="add_numbers", description="Adds two given numbers and returns the result")
def add_numbers(number1: float, number2: float) -> str:
    """Adds two given numbers and returns the result."""
    result = number1 + number2
    print(f"Adding {number1} + {number2} = {result}")
    return f"The sum of {number1} and {number2} is {result}"


@mcp.tool(name="get_temperature", description="Gets the current temperature for a given city")
def get_temperature(city: str) -> dict:
    """Gets the current temperature for a given city.

    Args:
        city (str): The name of the city (e.g., 'San Francisco').

    Returns:
        dict: A dictionary containing the temperature data or an error message.
    """
    print("Entered the method / function get_temperature");
    weatherAPIUrl = "http://api.weatherapi.com/v1/current.json?key=" + weatherAPIKey + "&q=" + city;
    print(weatherAPIUrl)
    response = requests.get(weatherAPIUrl)
    data = response.json()
    print(data)
    return data

@mcp.tool(name="get_currency_exchange_rates", description="Gets the currency exchange rates for a given currency")
# Function to get currency exchange rates
def get_currency_exchange_rates(currency: str) -> dict:
    """Gets the currency exchange rates for a given currency.

    Args:
        currency (str): The currency code (e.g., 'USD').

    Returns:
        dict: A dictionary containing the exchange rate data.
    """
    print("Entered the method / function get_currency_exchange_rates");
    # Where USD is the base currency you want to use
    url = 'https://v6.exchangerate-api.com/v6/6f9f5f76947ce2150d20b85c/latest/' + currency + "/"

    # Making our request
    response = requests.get(url)
    data = response.json()
    return data

@mcp.tool(name="get_stock_price", description="Gets the stock price for a given ticker symbol")
# Function to Get Stock Price
def get_stock_price(ticker: str) -> dict:
    """Gets the stock price for a given ticker symbol.

    Args:
        ticker (str): The stock ticker symbol (e.g., 'AAPL' for Apple).

    Returns:
        dict: A dictionary containing the stock price or an error message.
    """
    print("Entered the method / function get_stock_price");
    print(ticker)
    stock = yf.Ticker(ticker)
    hist = stock.history(period="1d")
    if not hist.empty:
        return {"price": str(hist['Close'].iloc[-1])}
    else:
        return {"error": "No data available"}

# STEP 3 : Define RESOUCES.
@mcp.resource(
    "docs://documents",
    mime_type="application/json"
)
def list_docs() -> list[str]:
    return list(docs.keys())

@mcp.resource(
    "docs://documents/{document_name}",
    mime_type="text/markdown"
)
def read_doc(document_name: str) -> str:
    if document_name not in docs:
        print(f"Document {document_name} not found.")
        raise ValueError(f"Document {document_name} not found.")
    return docs[document_name]


# STEP 4 - DEFINE PROMPTS
@mcp.prompt(
    name="format_doc_prompt",
    description="Rewrites the contents of the document in Markdown format."
)
def format_document(
    doc_id: str = Field(description="Id of the document to format")
) -> list[base.Message]:
    """Rewrites the contents of the document in Markdown format."""
    prompt = f"""
Your goal is to reformat a document to be written with markdown syntax.

The id of the document you need to reformat is:
<document_id>
{doc_id}
</document_id>

Add in headers, bullet points, tables, etc as necessary. Feel free to add in structure.
Use the 'edit_document' tool to edit the document. After the document has been reformatted...
"""
    
    return [
        base.UserMessage(prompt)
    ]

if __name__ == "__main__":
    mcp.run(transport="stdio")
    #This starts a development server and gives you a local URL, 
    # typically something like http://127.0.0.1:6274. 
    # Open this URL in your browser to access the MCP Inspector.
