from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import sop_parser, deviation_detector, behavioral_profiler, synthetic_generator, column_mapping
from app.config import settings

app = FastAPI(
    title="Loan SOP Compliance AI Service",
    description="AI microservice for SOP parsing, deviation detection, and behavioral profiling",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(sop_parser.router)
app.include_router(deviation_detector.router)
app.include_router(behavioral_profiler.router)
app.include_router(synthetic_generator.router)
app.include_router(column_mapping.router)

@app.get("/")
async def root():
    return {
        "message": "Loan SOP Compliance AI Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "sop_parsing": "/ai/sop",
            "deviation_detection": "/ai/deviation",
            "behavioral_profiling": "/ai/behavioral",
            "synthetic_generation": "/ai/synthetic",
            "column_mapping": "/ai/mapping"
        }
    }

@app.get("/ai/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "AI Service",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=True
    )
