from fastapi import FastAPI
from pydantic import BaseModel
import google.generativeai as genai
import os
import json

app = FastAPI()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')


class JudgeRequest(BaseModel):
    topic: str
    qa_pairs: list  # [{"question": "...", "answer": "..."}]

@app.post("/evaluate_quality")
def evaluate_quality(request: JudgeRequest):
    prompt = f"""You are an expert educational content evaluator. Evaluate the quality of
             answers for an educational course on: {request.topic}

            For each question-answer pair below, assess:
            1. ACCURACY: Is the answer factually correct?
            2. COMPLETENESS: Does it fully address the question?
            3. CLARITY: Is it well-explained and easy to understand?
            4. EXAMPLES: Does it include concrete examples or illustrations?
            5. EDUCATIONAL VALUE: Would a student learn effectively from this?

            Question-Answer Pairs:
            {json.dumps(request.qa_pairs, indent=2)}

            Return ONLY this JSON format (no markdown, no extra text):
            {{
            "approved": true/false,
            "overall_score": 0-10,
            "feedback": "Overall assessment and suggestions for improvement",
            "individual_evaluations": [
                {{
                "question_id": 1,
                "score": 0-10,
                "issues": ["list", "of", "problems"],
                "strengths": ["what", "was", "good"]
                }}
            ]
            }}

            Approval criteria: All answers must score 7+ to be approved.
            """
    # Call Gemini
    response = model.generate_content(prompt)
    
    # Clean markdown fences (you already know this!)
    response_text = response.text
    if response_text.startswith("```"):
        response_text = "\n".join(response_text.split("\n")[1:-1])

    # Parse JSON
    evaluation = json.loads(response_text.strip())

    return {
        "topic": request.topic,
        "evaluation": evaluation
    }


        

    

@app.get("/.well-known/agent.json")
def agent_card():
    return {
        "name": "quality_judge",
        "description": "Evaluates educational content quality",
        "capabilities": [{
            "name": "evaluate_quality",
            "description": "Assess answer quality and provide feedback",
            "input_schema": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "qa_pairs": {
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
                },
                "required": ["topic", "qa_pairs"]
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "approved": {"type": "boolean"},
                    "overall_score": {"type": "number"},
                    "feedback": {"type": "string"},
                    "individual_evaluations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "question_id": {"type": "integer"},
                                "score": {"type": "number"},
                                "issues": {"type": "array"},
                                "strengths": {"type": "array"}
                            }
                        }
                    }
                }
            }
        }]
    }


@app.get("/health")
def health():
    return {"status": "healthy"}