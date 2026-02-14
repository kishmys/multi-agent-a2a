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
    print("=" * 60)
    print("🚀 Multi-Agent Course Creator Starting")
    print("=" * 60)
    
    question_url = os.getenv("QUESTION_AGENT_URL", "http://question-agent:8080")
    answer_url = os.getenv("ANSWER_AGENT_URL", "http://answer-agent:8080")
    judge_url = os.getenv("JUDGE_AGENT_URL", "http://judge-agent:8080")
    
    registry.register_agent("question_generator", question_url)
    registry.register_agent("answer_generator", answer_url)
    registry.register_agent("quality_judge", judge_url)
    
    print("=" * 60)
    print("✅ All agents registered")
    print("=" * 60)

@app.post("/create_course")
def create_course(request: CourseRequest):
    start_time = time.time()
    
    print("\n" + "="*60)
    print(f"🎯 Creating Course: {request.topic}")
    print(f"📝 Questions: {request.num_questions} | Max Attempts: {request.max_retries}")
    print("="*60 + "\n")
    
    # Step 1: Generate questions
    print("Step 1: Generating questions...")
    questions_result = registry.call_agent(
        "question_generator",
        "generate_questions",
        {"topic": request.topic, "num_questions": request.num_questions}
    )
    print(f"✓ Generated {len(questions_result['questions'])} questions\n")
    
    # Step 2: Generate and evaluate answers with retry loop
    best_attempt = None
    best_score = 0
    feedback = None
    
    print("Step 2: Generating answers with quality evaluation...\n")
    
    for attempt in range(request.max_retries):
        print(f"Attempt {attempt + 1}/{request.max_retries}:")
        
        # Prepare answer input
        answer_input = {
            "topic": request.topic,
            "questions": questions_result["questions"]
        }
        if feedback:
            print(f"  → Using feedback from previous attempt")
            answer_input["feedback"] = feedback
        
        # Generate answers
        print("  → Generating answers...")
        answers_result = registry.call_agent(
            "answer_generator",
            "generate_answers",
            answer_input
        )
        print("  ✓ Answers generated")
        
        # Evaluate quality
        print("  → Evaluating quality...")
        evaluation = registry.call_agent(
            "quality_judge",
            "evaluate_quality",
            {
                "topic": request.topic,
                "qa_pairs": answers_result["answers"]
            }
        )
        
        # Extract evaluation data
        eval_data = evaluation["evaluation"]
        score = eval_data["overall_score"]
        approved = eval_data["approved"]
        
        # Track best attempt
        if score > best_score:
            best_score = score
            best_attempt = {
                "answers": answers_result["answers"],
                "evaluation": eval_data,
                "attempt": attempt + 1
            }
        
        # Check if approved
        if approved:
            print(f"  ✅ APPROVED! Score: {score}/10\n")
            break
        else:
            print(f"  ❌ Score: {score}/10 - Not approved")
            feedback = eval_data["feedback"]
            
            if attempt < request.max_retries - 1:
                print(f"  🔄 Retrying with feedback...\n")
            else:
                print(f"  ⚠️  Max retries reached. Using best attempt.\n")
    
    total_time = time.time() - start_time
    
    print("="*60)
    print(f"🎉 Course Complete!")
    print(f"📊 Final Score: {best_score}/10")
    print(f"🔢 Attempts: {best_attempt['attempt']}")
    print(f"⏱️  Time: {total_time:.2f}s")
    print("="*60 + "\n")
    
    return {
        "topic": request.topic,
        "course_content": best_attempt["answers"],
        "quality_evaluation": best_attempt["evaluation"],
        "attempts_needed": best_attempt["attempt"],
        "total_time_seconds": round(total_time, 2)
    }

@app.get("/agents")
def list_agents():
    return {name: agent["card"] for name, agent in registry.agents.items()}

@app.get("/health")
def health():
    return {"status": "healthy"}