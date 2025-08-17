# My MCP Server

This project is an MCP (Model-Context-Protocol) server that provides a set of tools for a large language model to interact with. These tools allow the model to perform various tasks, such as reading and writing documents, performing calculations, and fetching real-world data like weather, currency exchange rates, and stock prices.

## Features

The MCP server exposes the following tools:

- **`document_reader`**: Reads the content of a document.
- **`document_writer`**: Writes content to a document.
- **`document_editor`**: Edits a document.
- **`add_numbers`**: Adds two numbers.
- **`get_temperature`**: Gets the current temperature for a given city using the WeatherAPI.
- **`get_currency_exchange_rates`**: Gets currency exchange rates for a given currency using the ExchangeRate-API.
- **`get_stock_price`**: Gets the stock price for a given ticker symbol using the `yfinance` library.

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Create a virtual environment and install dependencies using `uv`:**
   The project is configured to use `uv`, a fast Python package installer. If you don't have `uv` installed, you can install it with:
   ```bash
   pip install uv
   ```
   Then, create the virtual environment and install the dependencies from `pyproject.toml`:
   ```bash
   uv venv
   uv pip install -r requirements.txt
   ```
   Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```

## Configuration

The project uses a `.env` file to manage API keys.

1. **Create a `.env` file** in the root of the project.
2. **Add the following environment variables** to the `.env` file:

   ```
   weatherAPIKey=<your_weather_api_key>
   exchangeRateAPIKey=<your_exchange_rate_api_key>
   ```

   Replace `<your_weather_api_key>` and `<your_exchange_rate_api_key>` with your actual API keys from [WeatherAPI](https://www.weatherapi.com/) and [ExchangeRate-API](https://www.exchangerate-api.com/) respectively.

## Usage

There are two primary ways to run the MCP server:

### 1. Using the `mcp dev` tool

For local development, you can use the `mcp dev` tool, which will start the server and automatically reload it when you make changes to the code.

```bash
mcp dev mcp_server.py
```

This will start a development server and give you a local URL, typically something like `http://127.0.0.1:6274`. You can open this URL in your browser to access the MCP Inspector.


```bash
mcp run mcp_server.py
```
This will start a MCP server in production mode.

```bash
mcp install mcp_server.py
```
This will install the MCP server config in the claude desktop.


### 2. Using `mcp.json` in Claude Desktop and Trae IDE

The `mcp.json` file in this project is configured to run the MCP server. IDEs like Claude Desktop and Trae IDE can use this file to run the server.

To run the server in these IDEs, you should be able to:
### For CLAUDE DESKTOP, follow the steps below

1. Open claude desktop or trae ide.
2. Select the claude `settings` 
3. Navigate to the `developer` section.
4. In the `developer` section, you should see an option to `Edit config`.
5. Open the edit config file.
6. In the edit config file, you should see a section for `mcpServers`.
7. Add the following configuration for the `document-mcp` server:
{
  "mcpServers": {
    "document-mcp": {
      "command": "/Users/bhogaai/.local/bin/uv",
      "args": [
        "run",
        "--project",
        "/Users/bhogaai/model-context-protocol",
        "/Users/bhogaai/model-context-protocol/mcp_server.py"
      ],
      "cwd": "/Users/bhogaai/model-context-protocol",
      "env": {
        "weatherAPIKey": "8e0a847b4161401da63140433250207",
        "PYTHONPATH": "/Users/bhogaai/model-context-protocol",
        "UV_PROJECT_ENVIRONMENT": "/Users/bhogaai/model-context-protocol/.venv"
      }
    }
  }
}
Restart the claude desktop.

### for TRAE IDE, follow the steps below.

1. In chat window type @ and select `builder with MCP`
2. Click tools icon and `Add more tools`
3. Then click 'Add' and select 'Add manually`
4. then copy the contents of `mcp.json` to configuration file.

### for GEMINI CLI, follow the steps below.
1. create a .gemini/settings.json file
2. add the following configuration to the file.
{
  "mcpServers": {
    "document-mcp": {
      "command": "/Users/bhogaai/.local/bin/uv",
      "args": [
        "run",
        "--project",
        "/Users/bhogaai/model-context-protocol",
        "/Users/bhogaai/model-context-protocol/mcp_server.py"
      ],
      "cwd": "/Users/bhogaai/model-context-protocol",
      "env": {
        "weatherAPIKey": "8e0a847b4161401da63140433250207",
        "PYTHONPATH": "/Users/bhogaai/model-context-protocol",
        "UV_PROJECT_ENVIRONMENT": "/Users/bhogaai/model-context-protocol/.venv"
      }
    }
  }
}
3. Restart the gemini cli.
4. Ask gemini CLI to start the mcp server 
5. You should see the mcp server started in the gemini cli.
6. You can now use the mcp server in the gemini cli.
7. To list tools, type /mcp list tools.
8. Then presse control+t to see the tools.
9. Then ask questions to the mcp server.
10. You should see the response from the mcp server.