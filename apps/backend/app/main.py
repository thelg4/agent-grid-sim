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
    title="Enhanced LangGraph Multiagent Simulation",
    description="A demonstration of LangGraph-based multiagent systems with conditional flows",
    version="2.0.0"
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
    logger.info("Enhanced simulation initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize simulation: {e}")
    # Don't raise here, let the app start and handle errors gracefully

# Response models
class GridResponse(BaseModel):
    width: int
    height: int
    cells: dict
    mission_phase: str
    exploration_progress: float
    buildings_built: int
    coordination_needed: bool
    emergency_mode: bool

class StepResponse(BaseModel):
    logs: list
    grid: dict
    agents: dict
    step_count: int
    mission_phase: str
    coordination_needed: bool
    emergency_mode: bool
    phase_transitions: list
    coordination_events: list

class ConditionalMetricsResponse(BaseModel):
    mission_phase: str
    phase_transitions: int
    coordination_events: int
    emergency_activations: int
    last_activity: dict
    coordination_needed: bool
    strategic_plan_ready: bool

@app.get("/")
async def root():
    return {
        "message": "Enhanced LangGraph Multiagent Simulation API",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "Conditional flows and routing",
            "Mission phase management", 
            "Emergency response coordination",
            "Dynamic agent collaboration",
            "Strategic planning workflows"
        ],
        "endpoints": [
            "/api/grid", "/api/logs", "/api/agents", "/api/step", 
            "/api/health", "/api/conditional-metrics", "/api/phase-info"
        ]
    }

@app.get("/api/health")
async def health_check():
    """Enhanced health check with conditional flow status."""
    try:
        if not sim:
            return {
                "status": "unhealthy",
                "error": "Simulation not initialized",
                "openai_configured": bool(os.getenv("OPENAI_API_KEY"))
            }
            
        # Enhanced health checks
        grid_state = sim.get_grid_state()
        agent_count = len(sim.get_agent_status())
        conditional_metrics = sim.get_conditional_metrics()
        
        return {
            "status": "healthy",
            "agents": agent_count,
            "grid_size": f"{grid_state['width']}x{grid_state['height']}",
            "mission_phase": conditional_metrics["mission_phase"],
            "coordination_active": conditional_metrics["coordination_needed"],
            "emergency_mode": conditional_metrics.get("active_threats", 0) > 0,
            "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
            "conditional_flows": "enabled"
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
    """Get current grid state with conditional flow information."""
    try:
        if not sim:
            raise HTTPException(status_code=500, detail="Simulation not initialized")
        
        grid_state = sim.get_grid_state()
        return grid_state
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
    """Get agent status information with conditional flow context."""
    try:
        if not sim:
            return {}
        return sim.get_agent_status()
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get agent status")

@app.post("/api/step")
async def step_simulation():
    """Execute one simulation step with conditional flow processing."""
    try:
        if not sim:
            raise HTTPException(status_code=500, detail="Simulation not initialized")
        
        result = sim.step()
        logger.info(f"Enhanced simulation step completed. Step: {result.get('step_count')}, "
                   f"Phase: {result.get('mission_phase')}, "
                   f"Coordination: {result.get('coordination_needed')}")
        return result
    except Exception as e:
        logger.error(f"Error during simulation step: {e}")
        raise HTTPException(status_code=500, detail=f"Simulation step failed: {str(e)}")

@app.get("/api/conditional-metrics")
async def get_conditional_metrics():
    """Get metrics specific to conditional flow behavior."""
    try:
        if not sim:
            raise HTTPException(status_code=500, detail="Simulation not initialized")
        
        metrics = sim.get_conditional_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Error getting conditional metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conditional metrics")

@app.get("/api/phase-info")
async def get_phase_info():
    """Get detailed information about current mission phase."""
    try:
        if not sim:
            raise HTTPException(status_code=500, detail="Simulation not initialized")
        
        from app.simulation import SimulationGoals
        
        step_count = sim.state.get("step_count", 0)
        mission_phase = sim.state.get("mission_phase", "initialization")
        
        phase_info = {
            "current_phase": mission_phase,
            "step_count": step_count,
            "current_objectives": SimulationGoals.get_current_objectives(step_count, mission_phase),
            "exploration_progress": sim.state.get("exploration_progress", 0.0),
            "buildings_built": sim.state.get("buildings_built", 0),
            "coordination_needed": sim.state.get("coordination_needed", False),
            "emergency_mode": sim.state.get("emergency_mode", False),
            "strategic_plan_ready": sim.state.get("strategic_plan_ready", False),
            "phase_transitions": sim.state.get("phase_transitions", []),
            "coordination_events": sim.state.get("coordination_events", []),
            "targets": {
                "exploration_target": SimulationGoals.EXPLORATION_TARGET,
                "building_target": SimulationGoals.BUILDING_TARGET,
                "max_steps": SimulationGoals.MAX_STEPS
            }
        }
        
        return phase_info
    except Exception as e:
        logger.error(f"Error getting phase info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get phase information")

@app.post("/api/trigger-emergency")
async def trigger_emergency():
    """Trigger emergency mode for testing conditional flows."""
    try:
        if not sim:
            raise HTTPException(status_code=500, detail="Simulation not initialized")
        
        sim.state["emergency_mode"] = True
        sim.state["active_threats"] = 1
        sim.state["logs"].append("🚨 MANUAL EMERGENCY TRIGGERED: Testing emergency response flows")
        
        logger.info("Emergency mode manually triggered for testing")
        return {
            "message": "Emergency mode activated",
            "emergency_mode": True,
            "active_threats": sim.state["active_threats"]
        }
    except Exception as e:
        logger.error(f"Error triggering emergency: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger emergency")

@app.post("/api/force-coordination")
async def force_coordination():
    """Force coordination mode for testing conditional flows."""
    try:
        if not sim:
            raise HTTPException(status_code=500, detail="Simulation not initialized")
        
        sim.state["coordination_needed"] = True
        sim.state["logs"].append("🤝 MANUAL COORDINATION TRIGGERED: Testing coordination flows")
        
        logger.info("Coordination mode manually triggered for testing")
        return {
            "message": "Coordination mode activated",
            "coordination_needed": True,
            "mission_phase": sim.state.get("mission_phase", "unknown")
        }
    except Exception as e:
        logger.error(f"Error forcing coordination: {e}")
        raise HTTPException(status_code=500, detail="Failed to force coordination")

@app.post("/api/reset")
async def reset_simulation():
    """Reset the simulation to initial state."""
    try:
        global sim
        sim = Simulation(
            width=int(os.getenv("GRID_WIDTH", 6)),
            height=int(os.getenv("GRID_HEIGHT", 5))
        )
        logger.info("Enhanced simulation reset successfully")
        return {"message": "Enhanced simulation reset successfully"}
    except Exception as e:
        logger.error(f"Error resetting simulation: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset simulation")
    
@app.get("/api/debug")
async def debug_info():
    """Enhanced debug endpoint with conditional flow information."""
    try:
        if not sim:
            return {"error": "Simulation not initialized"}
        
        # Get detailed agent information
        agents_debug = {}
        for agent_id, agent in sim.agents.items():
            agents_debug[agent_id] = {
                "basic_status": agent.get_status(),
                "memory_full": agent.memory,
                "memory_count": len(agent.memory),
                "position": sim.grid.get_agent_position(agent_id),
                "agent_class": type(agent).__name__,
                "last_activity": sim.state["last_activity"].get(agent_id, "none"),
            }
            
            # Add agent-specific debug info
            if hasattr(agent, 'buildings_completed'):
                agents_debug[agent_id]["buildings_completed"] = agent.buildings_completed
                agents_debug[agent_id]["last_built_location"] = getattr(agent, 'last_built_location', None)
                agents_debug[agent_id]["processed_messages"] = len(getattr(agent, 'processed_messages', set()))
            
            if hasattr(agent, 'visited_cells'):
                agents_debug[agent_id]["cells_visited"] = len(agent.visited_cells)
                agents_debug[agent_id]["visited_cells_list"] = list(agent.visited_cells)
            
            if hasattr(agent, 'suggested_locations'):
                agents_debug[agent_id]["build_orders_issued"] = len(agent.suggested_locations)
                agents_debug[agent_id]["suggested_locations"] = list(agent.suggested_locations)
                agents_debug[agent_id]["scout_reports"] = len(getattr(agent, 'scout_reports', []))
        
        # Enhanced grid debug info
        grid_debug = {
            "dimensions": f"{sim.grid.width}x{sim.grid.height}",
            "total_cells": sim.grid.width * sim.grid.height,
            "agent_positions": sim.grid.agent_positions,
            "cells_with_structures": [],
            "cells_with_agents": [],
        }
        
        # Find all cells with structures or agents
        for (x, y), cell in sim.grid.grid.items():
            if cell.structure:
                grid_debug["cells_with_structures"].append({
                    "position": (x, y),
                    "structure": cell.structure,
                    "occupied_by": cell.occupied_by
                })
            if cell.occupied_by:
                grid_debug["cells_with_agents"].append({
                    "position": (x, y),
                    "agent": cell.occupied_by,
                    "structure": cell.structure
                })
        
        # Enhanced simulation state debug
        sim_debug = {
            "step_count": sim.state.get("step_count", 0),
            "mission_status": sim.state.get("mission_status", "UNKNOWN"),
            "mission_phase": sim.state.get("mission_phase", "initialization"),
            "exploration_progress": sim._calculate_exploration_progress(),
            "buildings_built": sim._count_buildings(),
            "visited_cells_count": len(sim.visited_cells),
            "logs_count": len(sim.state.get("logs", [])),
            "recent_logs": sim.state.get("logs", [])[-5:],
            "coordination_needed": sim.state.get("coordination_needed", False),
            "emergency_mode": sim.state.get("emergency_mode", False),
            "strategic_plan_ready": sim.state.get("strategic_plan_ready", False),
            "phase_transitions": sim.state.get("phase_transitions", []),
            "coordination_events": sim.state.get("coordination_events", []),
        }
        
        return {
            "agents": agents_debug,
            "grid": grid_debug,
            "simulation": sim_debug,
            "conditional_metrics": sim.get_conditional_metrics(),
            "timestamp": "enhanced_debug_info_generated"
        }
        
    except Exception as e:
        logger.error(f"Debug endpoint error: {e}")
        return {"error": f"Debug failed: {str(e)}"}

@app.get("/api/grid-raw")
async def get_grid_raw():
    """Get raw grid data for debugging."""
    try:
        if not sim:
            return {"error": "Simulation not initialized"}
        
        # Return the raw grid state with all details
        raw_cells = {}
        for (x, y), cell in sim.grid.grid.items():
            raw_cells[f"{x},{y}"] = {
                "coordinates": (x, y),
                "occupied_by": cell.occupied_by,
                "structure": cell.structure,
                "cell_object": str(cell)
            }
        
        return {
            "width": sim.grid.width,
            "height": sim.grid.height,
            "agent_positions": sim.grid.agent_positions,
            "raw_cells": raw_cells,
            "serialized_cells": sim.grid.serialize(),
            "bounds_check": {
                "max_x": sim.grid.width - 1,
                "max_y": sim.grid.height - 1,
                "example_valid_coords": [(0, 0), (sim.grid.width-1, sim.grid.height-1)]
            },
            "conditional_state": sim.get_conditional_metrics()
        }
        
    except Exception as e:
        logger.error(f"Grid raw endpoint error: {e}")
        return {"error": f"Grid raw failed: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)