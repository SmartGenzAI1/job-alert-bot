# App alias for deployment compatibility
# This file allows the application to be deployed with both uvicorn and gunicorn

from main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)