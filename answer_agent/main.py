from fastapi import FastAPI
from pydantic import BaseModel
import google.generativeai as genai
import os
import json

app = FastAPI()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

class AnswerRequest(BaseModel):
    questions: list  # List of question objects from Question Agent
    topic: str
    feedback: str = None

@app.post("/generate_answers")
def generate_answers(request: AnswerRequest):
    # Build the prompt with actual questions
    questions_text = "\n".join([
        f"{q['id']}. {q['question']}" 
        for q in request.questions
    ])
    
    prompt = f"""You are an expert educator on the topic: {request.topic}

    Below are questions that need comprehensive, educational answers:

    {questions_text}

    {"PREVIOUS ATTEMPT FEEDBACK: " + request.feedback + """

    Please IMPROVE your answers based on this feedback. Address the issues mentioned and enhance the quality.
    """ if request.feedback else ""}

    Provide detailed answers for each question. Return ONLY a JSON array matching this format:
    [
    {{"id": 1, "question": "original question here", "answer": "comprehensive answer here"}},
    {{"id": 2, "question": "original question here", "answer": "comprehensive answer here"}}
    ]

    No other text, just the JSON array."""

    # Call Gemini
    response = model.generate_content(prompt)
    
    # Clean markdown fences (you already know this!)
    response_text = response.text
    if response_text.startswith("```"):
        response_text = "\n".join(response_text.split("\n")[1:-1])
    
    # Parse JSON
    answers = json.loads(response_text.strip())
    
    return {
        "topic": request.topic,
        "answers": answers
    }

@app.get("/.well-known/agent.json")
def agent_card():
    return {
        "name": "answer_generator",
        "description": "Generates comprehensive educational answers",
        "capabilities": [{
            "name": "generate_answers",
            "description": "Create detailed answers for educational questions",
            "input_schema": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "questions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer"},
                                "question": {"type": "string"}
                            }
                        }
                    }
                },
                "required": ["topic", "questions"]
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "answers": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer"},
                                "question": {"type": "string"},
                                "answer": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }],
        "url": "http://localhost:8002"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}