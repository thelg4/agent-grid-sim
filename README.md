# LangGraph Multiagent System Demo

A practical demonstration of building multiagent systems using LangGraph, featuring autonomous agents that explore, plan, and build in a shared grid environment.

## 🎯 What This Demonstrates

- **LangGraph Integration**: Practical implementation of LangGraph for agent coordination
- **LLM-Powered Agents**: Each agent uses GPT-4o for intelligent decision making
- **Real-time Visualization**: Live grid updates showing agent positions and actions
- **Agent Communication**: Structured message passing between agents
- **Role-based Behavior**: Specialized agents with distinct capabilities

## 🤖 Agents

### Scout Agent 👀
- **Role**: Exploration and reconnaissance
- **Capabilities**: Move around the grid, observe surroundings, report findings
- **Behavior**: Systematically explores unvisited areas

### Builder Agent 🔨
- **Role**: Construction and building
- **Capabilities**: Build structures at specified coordinates
- **Behavior**: Responds to strategist suggestions and identifies good building spots

### Strategist Agent 🧠
- **Role**: Planning and coordination
- **Capabilities**: Analyze grid state, suggest optimal building locations
- **Behavior**: Makes strategic decisions based on scout reports and grid analysis

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- OpenAI API key

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd agent-grid-sim
```

### 2. Backend Setup

```bash
cd apps/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### 3. Frontend Setup

```bash
cd apps/frontend

# Install dependencies
npm install
```

### 4. Run the Application

**Terminal 1 - Backend:**
```bash
cd apps/backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd apps/frontend
npm run dev
```

Visit http://localhost:5173 to see the simulation in action!

## 🔧 Configuration

### Environment Variables

Create `apps/backend/.env`:

```bash
