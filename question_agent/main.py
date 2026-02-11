from fastapi import FastAPI
from pydantic import BaseModel
import google.generativeai as genai
import os
import json

app = FastAPI()

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

# Define what data we expect
class QuestionRequest(BaseModel):
    topic: str
    num_questions: int = 3

@app.post("/generate_questions")
def generate_questions(request: QuestionRequest):
    """
    This agent generates questions about a topic.
    
    TODO: You need to fill this in!
    
    Steps:
    1. Create a prompt asking Gemini to generate questions
    2. Call the model
    3. Return the questions in a structured format
    """
    
    # YOUR CODE HERE
    prompt = f"""Generate {request.num_questions} educational questions about: {request.topic}

    Return ONLY a JSON array with this exact format:
    [
    {{"id": 1, "question": "What is...?"}},
    {{"id": 2, "question": "How does...?"}},
    {{"id": 3, "question": "Why is...?"}}
    ]

    No other text, just the JSON array."""  # What prompt would you write?
    
    # Call Gemini
    response = model.generate_content(prompt)
    

    # parse the respone
    # DEBUG: Let's see what we actually got

    # Strip markdown code fences properly
    response_text = response.text
    if response_text.startswith("```"):
        # Remove first line (```json or ```)
        response_text = response_text.split("\n", 1)[1]
    if response_text.endswith("```"):
        # Remove last line
        response_text = response_text.rsplit("\n", 1)[0]

    cleaned_text = response_text.strip()
    # print(f"DEBUG - Response text: {cleaned_text}")
    # print(f"DEBUG - Response type: {type(cleaned_text)}")

    questions = json.loads(cleaned_text)

    # Return structured data
    return {
        "topic": request.topic,
        "questions": questions  # What goes here?
    }


    # Expose agent card at /.well-known/agent.json
    
# question_agent/main.py - Updated agent_card()
@app.get("/.well-known/agent.json")
def agent_card():
    return {
        "name": "question_generator",
        "description": "Generates educational questions",
        "capabilities": [{
            "name": "generate_questions",
            "description": "Create questions on any topic",
            "input_schema": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "num_questions": {"type": "integer", "default": 3}
                },
                "required": ["topic"]
            },
            "output_schema": {
                "type": "object",
                "properties": {
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
                }
            }
        }],
        "url": "http://localhost:8001"
    }

# Health check endpoint
@app.get("/health")
def health():
    return {"status": "healthy"}