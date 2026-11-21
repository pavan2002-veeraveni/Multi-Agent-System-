"""
API Interface compatibility module
Exposes `app` from `main` for backward compatibility with uvicorn or existing integrations.
"""

from main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
