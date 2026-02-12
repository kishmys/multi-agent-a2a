from fastapi import FastAPI
from pydantic import BaseModel
import requests
import os

app = FastAPI()

class AgentRegistry:
    """Manages agent discovery and communication."""
    
    def __init__(self):
        self.agents = {}
    
    def register_agent(self, name: str, base_url: str):
        """Fetch and store agent card."""
        card_url = f"{base_url}/.well-known/agent.json"
        response = requests.get(card_url)
        self.agents[name] = {
            "card": response.json(),
            "base_url": base_url
        }
        print(f"✓ Registered agent: {name}")
    
    def call_agent(self, agent_name: str, capability: str, input_data: dict):
        """Call an agent's capability."""
        if agent_name not in self.agents:
            raise ValueError(f"Agent {agent_name} not found")
        
        agent = self.agents[agent_name]
        base_url = agent["base_url"]
        
        endpoint = f"{base_url}/{capability}"
        response = requests.post(endpoint, json=input_data)
        return response.json()

# Global registry
registry = AgentRegistry()

class CourseRequest(BaseModel):
    topic: str
    num_questions: int = 3

@app.on_event("startup")
async def startup_event():
    """Register agents on startup using environment variables."""
    question_url = os.getenv("QUESTION_AGENT_URL")
    answer_url = os.getenv("ANSWER_AGENT_URL")
    
    if question_url:
        registry.register_agent("question_generator", question_url)
    if answer_url:
        registry.register_agent("answer_generator", answer_url)

@app.post("/create_course")
def create_course(request: CourseRequest):
    """Orchestrate multi-agent workflow."""
    
    questions_result = registry.call_agent(
        "question_generator",
        "generate_questions",
        {"topic": request.topic, "num_questions": request.num_questions}
    )
    
    answers_result = registry.call_agent(
        "answer_generator",
        "generate_answers",
        {
            "topic": request.topic,
            "questions": questions_result["questions"]
        }
    )
    
    return {
        "topic": request.topic,
        "course_content": answers_result["answers"]
    }

@app.get("/agents")
def list_agents():
    """See all registered agents."""
    return {
        name: agent["card"] 
        for name, agent in registry.agents.items()
    }

@app.get("/health")
def health():
    return {"status": "healthy"}