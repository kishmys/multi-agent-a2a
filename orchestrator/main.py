# orchestrator/main.py
from fastapi import FastAPI
from pydantic import BaseModel
import requests
import os
import time
app = FastAPI()

class AgentRegistry:
    def __init__(self):
        self.agents = {}

    def register_agent(self, name: str, base_url: str, retries=5):
        card_url = f"{base_url}/.well-known/agent.json"
        
        for attempt in range(retries):
            try:
                response = requests.get(card_url, timeout=2)
                self.agents[name] = {
                    "card": response.json(),
                    "base_url": base_url
                }
                print(f"✓ Registered agent: {name}")
                return
            except Exception as e:
                if attempt < retries - 1:
                    print(f"Waiting for {name} to be ready... (attempt {attempt + 1})")
                    time.sleep(2)
                else:
                    raise
    
    def call_agent(self, agent_name: str, capability: str, input_data: dict):
        if agent_name not in self.agents:
            raise ValueError(f"Agent {agent_name} not found")
        
        agent = self.agents[agent_name]
        base_url = agent["base_url"]
        endpoint = f"{base_url}/{capability}"
        response = requests.post(endpoint, json=input_data)
        return response.json()

registry = AgentRegistry()

class CourseRequest(BaseModel):
    topic: str
    num_questions: int = 3
    max_retries: int = 3

@app.on_event("startup")
async def startup_event():
    question_url = os.getenv("QUESTION_AGENT_URL", "http://question-agent:8080")
    answer_url = os.getenv("ANSWER_AGENT_URL", "http://answer-agent:8080")
    judge_url = os.getenv("JUDGE_AGENT_URL", "http://judge-agent:8080")
    
    registry.register_agent("question_generator", question_url)
    registry.register_agent("answer_generator", answer_url)
    registry.register_agent("quality_judge", judge_url)

@app.post("/create_course")
def create_course(request: CourseRequest):
    # Print workflow to console (visible in docker logs and terminal)
    print("\n" + "="*60)
    print(f"🎯 Creating Course: {request.topic}")
    print(f"📝 Questions: {request.num_questions} | Max Attempts: {request.max_retries}")
    print("="*60 + "\n")
    
    # Step 1
    print("Step 1: Generating questions...")
    questions_result = registry.call_agent(...)
    print(f"✓ Generated {len(questions_result['questions'])} questions\n")
    
    # Step 2
    print("Step 2: Generating answers with quality evaluation...\n")
    
    for attempt in range(request.max_retries):
        print(f"Attempt {attempt + 1}/{request.max_retries}:")
        
        # Generate
        print("  → Generating answers...")
        answers_result = registry.call_agent(...)
        print("  ✓ Answers generated")
        
        # Evaluate
        print("  → Evaluating quality...")
        evaluation = registry.call_agent(...)
        eval_data = evaluation["evaluation"]
        
        if eval_data["approved"]:
            print(f"  ✅ Approved! Score: {eval_data['overall_score']}/10\n")
            break
        else:
            print(f"  ❌ Score: {eval_data['overall_score']}/10 - Retrying...\n")
    
    print("="*60)
    print(f"🎉 Course Complete! Final Score: {best_score}/10")
    print("="*60 + "\n")
    
    # Return clean, readable response
    return {
        "success": True,
        "topic": request.topic,
        "quality_score": f"{best_score}/10",
        "attempts_used": best_attempt["attempt"],
        "course": best_attempt["answers"]
    }

@app.get("/agents")
def list_agents():
    return {name: agent["card"] for name, agent in registry.agents.items()}

@app.get("/health")
def health():
    return {"status": "healthy"}