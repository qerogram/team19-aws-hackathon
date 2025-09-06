# SQL Data Analysis Agent

A production-ready ReAct (Reasoning and Acting) agent that provides natural language interface for SQL database analysis. Built with LangChain, FastAPI, and supports multiple LLM providers including AWS Bedrock, OpenAI, and Anthropic.

## Features

- **ReAct Pattern Implementation**: Autonomous reasoning and action execution for complex data analysis tasks
- **Multi-LLM Support**: Seamless integration with AWS Bedrock, OpenAI, and Anthropic models
- **Rate Limit Protection**: Built-in throttling mechanism to prevent API rate limit errors
- **Natural Language Interface**: Ask questions in plain language and receive SQL queries with insights
- **RESTful API**: FastAPI-based server with automatic documentation
- **Database Schema Analysis**: Automatic schema discovery and intelligent query generation

## Architecture

### Core Components

- **agent.py**: Main agent implementation with ReAct pattern and throttle control
- **app.py**: FastAPI server with async endpoints
- **tools.py**: Database interaction tools (schema inspection, query execution)
- **providers.py**: LLM provider abstractions for multi-model support
- **prompts.py**: ReAct prompt templates
- **client.py**: Command-line client for API interaction

### Throttle Protection

The system implements a callback-based throttling mechanism to prevent rate limit errors:
- Configurable delay between LLM calls (default: 3 seconds)
- Automatic sleep injection before each LLM invocation
- Prevents ThrottlingException from AWS Bedrock and other providers

## Prerequisites

- Python 3.8+
- PostgreSQL database
- AWS credentials (for Bedrock)
- API keys for OpenAI/Anthropic (optional)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd data-agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables in `.env`:
```bash
# Database Configuration
DB_HOST=your_db_host
DB_PORT=5432
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password

# AWS Configuration (for Bedrock)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1

# Optional: Other LLM Providers
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
```

## Usage

### Starting the Server

```bash
python app.py
```

The server will start on `http://localhost:5000`

### API Endpoints

#### Health Check
```bash
GET /health
```

#### Query Endpoint
```bash
POST /query
Content-Type: application/json

{
  "question": "What are the total sales for yesterday?",
  "provider": "bedrock",  # Options: bedrock, openai, anthropic
  "model": "us.anthropic.claude-sonnet-4-20250514-v1:0"  # Optional
}
```

#### Reinitialize Agent
```bash
POST /reinitialize
Content-Type: application/json

{
  "provider": "bedrock",
  "model": "us.anthropic.claude-sonnet-4-20250514-v1:0"
}
```

### Using the CLI Client

Interactive mode:
```bash
python client.py
```

Single query:
```bash
python client.py -q "Show me the top 5 bestselling products"
```

Health check:
```bash
python client.py --health
```

### Example Queries

- "Show me the database schema"
- "What tables are available?"
- "Calculate yesterday's total revenue"
- "List top 10 customers by purchase amount"
- "Show me the daily average order value for the last week"
- "Which product categories generate the most revenue?"
- "Analyze user engagement patterns by device type"

## Supported LLM Models

### AWS Bedrock
- Claude 3.5 Sonnet: `anthropic.claude-3-5-sonnet-20240620-v1:0`
- Claude Sonnet 4: `us.anthropic.claude-sonnet-4-20250514-v1:0` (requires inference profile)

### OpenAI
- GPT-3.5 Turbo: `gpt-3.5-turbo`
- GPT-4: `gpt-4`

### Anthropic
- Claude 3 Sonnet: `claude-3-sonnet-20240229`

## API Documentation

When the server is running, visit:
- Swagger UI: `http://localhost:5000/docs`
- ReDoc: `http://localhost:5000/redoc`

## Performance Considerations

### Rate Limits
- Default throttle delay: 3 seconds between LLM calls
- Adjustable in `agent.py` via `ThrottleCallbackHandler(delay_seconds=3.0)`
- Recommended for complex queries with multiple reasoning steps

### AWS Bedrock Quotas
- Default: 50 requests/minute for on-demand
- Consider requesting quota increases for production use
- Use Service Quotas console for adjustable quotas

## Troubleshooting

### ThrottlingException
If you encounter `ThrottlingException` errors:
1. Increase the throttle delay in `agent.py`
2. Request AWS Bedrock quota increases
3. Use simpler queries to reduce LLM calls
4. Wait between consecutive API requests

### Database Connection Issues
- Verify PostgreSQL is running
- Check `.env` database credentials
- Ensure database user has necessary permissions

## Project Structure

```
data-agent/
├── agent.py         # ReAct agent with throttle control
├── app.py           # FastAPI server
├── client.py        # CLI client
├── tools.py         # Database tools
├── providers.py     # LLM providers
├── prompts.py       # ReAct prompts
├── requirements.txt # Dependencies
├── .env.example     # Environment template
└── README.md        # Documentation
```

## License

MIT License

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.