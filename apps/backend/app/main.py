import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Load environment variables FIRST
load_dotenv()

# Now import your modules after env vars are loaded
from app.simulation import Simulation

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Verify OpenAI API key is loaded
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    logger.error("OPENAI_API_KEY not found in environment variables!")
    raise ValueError("OPENAI_API_KEY environment variable is required")
else:
    logger.info(f"OpenAI API key loaded: {openai_key[:10]}...")

app = FastAPI(
    title="LangGraph Multiagent Simulation",
    description="A demonstration of LangGraph-based multiagent systems",
    version="1.0.0"
)

# Fixed CORS configuration - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize simulation with error handling
sim = None
try:
    sim = Simulation(
        width=int(os.getenv("GRID_WIDTH", 6)),
        height=int(os.getenv("GRID_HEIGHT", 5))
    )
    logger.info("Simulation initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize simulation: {e}")
    # Don't raise here, let the app start and handle errors gracefully

# Response models
class GridResponse(BaseModel):
    width: int
    height: int
    cells: dict

class StepResponse(BaseModel):
    logs: list
    grid: dict
    agents: dict
    step_count: int

@app.get("/")
async def root():
    return {
        "message": "LangGraph Multiagent Simulation API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": ["/api/grid", "/api/logs", "/api/agents", "/api/step", "/api/health"]
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    try:
        if not sim:
            return {
                "status": "unhealthy",
                "error": "Simulation not initialized",
                "openai_configured": bool(os.getenv("OPENAI_API_KEY"))
            }
            
        # Basic health checks
        grid_state = sim.get_grid_state()
        agent_count = len(sim.get_agent_status())
        
        return {
            "status": "healthy",
            "agents": agent_count,
            "grid_size": f"{grid_state['width']}x{grid_state['height']}",
            "openai_configured": bool(os.getenv("OPENAI_API_KEY"))
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "openai_configured": bool(os.getenv("OPENAI_API_KEY"))
        }

@app.get("/api/grid")
async def get_grid():
    """Get current grid state."""
    try:
        if not sim:
            raise HTTPException(status_code=500, detail="Simulation not initialized")
        return sim.get_grid_state()
    except Exception as e:
        logger.error(f"Error getting grid state: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get grid state: {str(e)}")

@app.get("/api/logs")
async def get_logs():
    """Get simulation logs."""
    try:
        if not sim:
            return {"logs": ["Simulation not initialized"]}
        return {"logs": sim.get_logs()}
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get logs")

@app.get("/api/agents")
async def get_agents():
    """Get agent status information."""
    try:
        if not sim:
            return {}
        return sim.get_agent_status()
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get agent status")

@app.post("/api/step")
async def step_simulation():
    """Execute one simulation step."""
    try:
        if not sim:
            raise HTTPException(status_code=500, detail="Simulation not initialized")
        result = sim.step()
        logger.info(f"Simulation step completed. Step count: {result.get('step_count', 'unknown')}")
        return result
    except Exception as e:
        logger.error(f"Error during simulation step: {e}")
        raise HTTPException(status_code=500, detail=f"Simulation step failed: {str(e)}")

@app.post("/api/reset")
async def reset_simulation():
    """Reset the simulation to initial state."""
    try:
        global sim
        sim = Simulation(
            width=int(os.getenv("GRID_WIDTH", 6)),
            height=int(os.getenv("GRID_HEIGHT", 5))
        )
        logger.info("Simulation reset successfully")
        return {"message": "Simulation reset successfully"}
    except Exception as e:
        logger.error(f"Error resetting simulation: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset simulation")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)