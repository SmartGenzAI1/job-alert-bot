# ASGI configuration for deployment compatibility
# This ensures the application works with both uvicorn and gunicorn (with uvicorn workers)

from main import app

# For gunicorn with uvicorn workers: gunicorn asgi:app -k uvicorn.workers.UvicornWorker
# For uvicorn directly: uvicorn asgi:app --host 0.0.0.0 --port 8000

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)