from fastapi import FastAPI
from pydantic import BaseModel
import requests

app = FastAPI()

# Agent endpoints
QUESTION_AGENT_URL = "http://localhost:8001/generate_questions"
ANSWER_AGENT_URL = "http://localhost:8002/generate_answers"

class CourseRequest(BaseModel):
    topic: str
    num_questions: int = 3

@app.post("/create_course")
def create_course(request: CourseRequest):
    # Step 1: Get questions
    question_response = requests.post(
        QUESTION_AGENT_URL,
        json={"topic": request.topic, "num_questions": request.num_questions}
    )
    questions_data = question_response.json()
    
    # Step 2: Get answers
    answer_response = requests.post(
        ANSWER_AGENT_URL,
        json={"topic": request.topic, "questions": questions_data["questions"]}
    )
    answers_data = answer_response.json()
    
    # Step 3: Combine and return
    return {
        "topic": request.topic,
        "course_content": answers_data["answers"]
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)