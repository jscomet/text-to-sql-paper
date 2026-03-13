# Text-to-SQL Backend

FastAPI-based backend for Text-to-SQL conversion prototype.

## Features

- FastAPI web framework
- SQLAlchemy ORM with async support
- JWT authentication
- LLM API integration (OpenAI, Anthropic, vLLM, DeepSeek, DashScope)
- Alembic database migrations
- Universal LLM client (3 format types: openai/anthropic/vllm)

## Quick Start

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
copy .env.example .env
# Edit .env with your configuration
```

### 4. Run Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Access API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
backend/
├── app/
│   ├── core/          # Core configuration
│   ├── api/           # API routes
│   ├── models/        # Database models
│   ├── schemas/       # Pydantic schemas
│   └── utils/         # Utility functions
├── alembic/           # Database migrations
├── tests/             # Test files
└── requirements.txt   # Dependencies
```

## Development

### Code Formatting

```bash
black app/
isort app/
flake8 app/
```

### Run Tests

```bash
pytest
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection URL | `sqlite:///./app.db` |
| `SECRET_KEY` | JWT secret key | `your-secret-key-change-in-production` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiry | `60` |
| **Generic LLM Config** ||
| `LLM_PROVIDER` | Provider name (display only) | `openai` |
| `LLM_BASE_URL` | API base URL | `None` |
| `LLM_API_KEY` | API key | `None` |
| `LLM_MODEL` | Default model | `gpt-3.5-turbo` |
| `LLM_FORMAT` | API format: openai/anthropic/vllm | `openai` |
| **Legacy Provider Config (optional)** ||
| `OPENAI_API_KEY` | OpenAI API key | `None` |
| `DASHSCOPE_API_KEY` | DashScope API key | `None` |
| `DEEPSEEK_API_KEY` | DeepSeek API key | `None` |
| `ENVIRONMENT` | Environment (development/production) | `development` |
| `LOG_LEVEL` | Logging level | `INFO` |
