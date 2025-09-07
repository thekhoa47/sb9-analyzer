from app.core.app import create_app

# Create the FastAPI application
app = create_app()


# ---------- Health ----------
@app.get("/health")
def health():
    return {"ok": True}
