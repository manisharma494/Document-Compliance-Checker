# Document Compliance API

AI-powered system that processes PDF/DOCX documents and checks compliance against English guidelines using LanguageTool.

## Features

- **Document Analysis**: Upload PDF/DOCX files and get detailed grammar/compliance reports
- **Document Correction**: Automatically fix grammar issues and download corrected DOCX
- **Web Frontend**: Beautiful drag-and-drop interface for easy file uploads
- **REST API**: Programmatic access via POST endpoints
- **Multiple Formats**: Support for PDF and DOCX files

## Quick Start

### 1. Setup Environment
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r "Kelton project/requirements.txt"
```

### 2. Start the Server
```bash
# Start the API server
uvicorn app_api:app --port 8000 --reload
```

### 3. Access the Application
- **Web Frontend**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Usage

### Web Frontend (Recommended for Testing)

1. Open http://localhost:8000 in your browser
2. Drag & drop a PDF or DOCX file, or click "Choose File"
3. Click "🔍 Analyze Document" to see grammar issues
4. Click "✏️ Modify Document" to download corrected version

### API Endpoints

#### Analyze Document
```bash
curl -X POST http://localhost:8000/analyze \
  -F "file=@your_document.pdf"
```

**Response:**
```json
{
  "file_name": "your_document.pdf",
  "num_issues": 3,
  "issues": [
    {
      "message": "Possible agreement error.",
      "rule": "GRAMMAR",
      "offset": 12,
      "length": 4,
      "replacements": ["are", "is"],
      "context": "This are a sentence..."
    }
  ]
}
```

#### Modify Document
```bash
curl -X POST http://localhost:8000/modify \
  -F "file=@your_document.docx" \
  --output corrected_document.docx
```

**Response:** Downloads corrected DOCX file

### Python Client Example
```python
import requests

# Analyze document
with open("document.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/analyze",
        files={"file": ("document.pdf", f, "application/pdf")}
    )
    result = response.json()
    print(f"Found {result['num_issues']} issues")

# Modify document
with open("document.docx", "rb") as f:
    response = requests.post(
        "http://localhost:8000/modify",
        files={"file": ("document.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    )
    with open("corrected.docx", "wb") as out:
        out.write(response.content)
```

## Testing

### Run Test Suite
```bash
pytest -q
```

### Create Test Document
```bash
python "Kelton project/create_test_doc.py"
```

### Manual API Testing
```bash
# Test analyze endpoint
curl -X POST http://localhost:8000/analyze \
  -F "file=@test_document.docx"

# Test modify endpoint
curl -X POST http://localhost:8000/modify \
  -F "file=@test_document.docx" \
  --output corrected.docx
```

## Project Structure

```
Kelton project/
├── app/
│   ├── main.py              # FastAPI application
│   ├── services/
│   │   ├── extract.py       # PDF/DOCX text extraction
│   │   ├── checker.py       # LanguageTool compliance checker
│   │   └── modify.py        # Document correction & export
│   └── __init__.py
├── static/
│   └── index.html           # Web frontend
├── tests/
│   └── test_api.py          # API tests
├── app_api.py               # ASGI entry point
├── requirements.txt          # Python dependencies
├── create_test_doc.py       # Test document generator
└── README.md                # This file
```

## API Specifications

### Supported File Types
- **PDF** (.pdf) - Text extraction via pdfminer.six
- **DOCX** (.docx) - Text extraction via python-docx

### Error Handling
- Invalid file types return HTTP 400
- Empty documents return HTTP 400
- LanguageTool failures gracefully fall back to no issues

### CORS
- Enabled for all origins (development-friendly)
- Supports cross-origin requests from web clients

## Dependencies

- **FastAPI**: Modern web framework
- **LanguageTool**: Grammar and style checking
- **pdfminer.six**: PDF text extraction
- **python-docx**: DOCX file handling
- **pytest**: Testing framework

## Troubleshooting

### Common Issues

1. **"No module named 'app'"**
   - Ensure server is running with `uvicorn app_api:app --port 8000`

2. **"Unsupported file type"**
   - Only PDF and DOCX files are supported

3. **Port already in use**
   - Use different port: `uvicorn app_api:app --port 8001`

4. **Frontend not loading**
   - Check `static/index.html` exists
   - Verify server is running

### Server Status
```bash
# Check if server is running
curl http://localhost:8000/health

# Should return: {"status": "ok"}
```

## Development

### Adding New Features
1. Update services in `app/services/`
2. Add endpoints in `app/main.py`
3. Update tests in `tests/test_api.py`
4. Test with `pytest -q`

### Code Quality
- All code passes linter checks
- Tests cover main functionality
- Error handling for edge cases

## License

This project is created for the AI Python Developer Assessment.

