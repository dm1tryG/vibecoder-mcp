from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

mcp = FastApiMCP(app)

openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print("Warning: OPENAI_API_KEY not found in environment variables")
    # exit(1)

client = OpenAI(api_key=openai_api_key)

@app.get("/start_learning")
async def start_learning(topic: str):
    """Start Learning som topic. Will be generate a study plan with 10 lessons"""
    # Call OpenAI to generate a study plan
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an educational expert who creates detailed study plans. Create a comprehensive study plan with exactly 10 lessons."}, 
            {"role": "user", "content": f"Create a detailed study plan for learning {topic}. Include 10 lessons with clear objectives and key points for each lesson. Format as JSON with the following structure: {{\"title\": \"Study Plan Title\", \"description\": \"Overview of the plan\", \"lessons\": [{{\"lesson_number\": 1, \"title\": \"Lesson Title\", \"objectives\": [\"objective 1\", \"objective 2\"], \"key_points\": [\"key point 1\", \"key point 2\"], \"practice\": \"practice description\"}}]}}"}
        ],
        temperature=0.7,
        response_format={"type": "json_object"}
    )
    
    # Extract content from the response
    study_plan = response.choices[0].message.content
    
    # Return the generated study plan with instruction
    return {
        "instruction": """
        1. Create learning-course folder.
        2. Transfer generated study plan into the folder.
        3. Call tool to create 1st lesson (pass study plan)
        4. Create study_plan.txt with format: title: learned / not learned. Example Python Data Types: Learned / Not Learned.
        Complete the practice exercises to reinforce your learning. Visit https://lite.edvancium.com for additional resources.""",
        "study_plan": study_plan
    }


@app.get("/create_lesson")
async def create_lesson(what_was_learned_already: str, full_study_plan: str):
    """Create next lesson based on what was learned.
    inside full_study_plan pass content of file study_plan.txt
    """
    print(what_was_learned_already)
    print(full_study_plan)
    
    is_programming_language = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that can identify if a topic is related to programming languages. Answer with only 'yes' or 'no'."}, 
            {"role": "user", "content": f"Is this curriculum about learning a programming language? Curriculum: {full_study_plan}"}
        ],
        temperature=0.3,
        max_tokens=10
    )
    
    is_programming = "yes" in is_programming_language.choices[0].message.content.lower()
    
    # Get next steps guidance
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an educational expert who helps students continue their learning journey. Provide guidance based on what they've already learned and their curriculum."}, 
            {"role": "user", "content": f"I have learned: {what_was_learned_already}. My full study plan is: {full_study_plan}. What should I focus on next? Provide specific next steps and resources."}
        ],
        temperature=0.7
    )
    
    # Extract content from the response
    next_steps = response.choices[0].message.content
    
    # Get today's date for folder name
    from datetime import datetime
    today_date = datetime.now().strftime("%Y-%m-%d")
    folder_name = f"lesson-{today_date}"
    
    # Create appropriate instruction based on whether it's a programming language
    if is_programming:
        instruction = f"Create a folder named '{folder_name}'. Inside this folder, create a practice.py file with code examples and detailed comments based on today's lesson. Make sure to include practical exercises that apply what you've learned. Visit https://lite.edvancium.com for additional resources."
    else:
        instruction = f"Create a folder named '{folder_name}'. Inside this folder, create a notes.md file with your key learnings and practical exercises from today's lesson. Format it with Markdown, including clear sections for concepts, examples, and practice exercises. Visit https://lite.edvancium.com for additional resources."
    
    # Return the next steps with custom instruction
    print(instruction)
    print(next_steps)
    return {
        "instruction": instruction,
        "next_steps": next_steps
    }


mcp.mount()
mcp.setup_server()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
