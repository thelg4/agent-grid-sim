# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.simulation import Simulation

app = FastAPI()
sim = Simulation()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust as needed for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/grid")
def get_grid():
    return sim.get_grid_state()

@app.get("/api/logs")
def get_logs():
    return {"logs": sim.get_logs()}

@app.get("/api/agents")
def get_agents():
    return sim.get_agent_status()

@app.post("/api/step")
def step_simulation():
    result = sim.step()
    return result
