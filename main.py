from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import sqlite3
import google.generativeai as genai

app = FastAPI()

GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

def init_db():
    conn = sqlite3.connect('fitness.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age INTEGER,
            weight REAL,
            goal TEXT,
            intensity TEXT,
            workout_plan TEXT,
            nutrition_tip TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_ai_response(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return None

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate", response_class=HTMLResponse)
def generate(request: Request,
    name: str = Form(...),
    age: int = Form(...),
    weight: float = Form(...),
    goal: str = Form(...),
    intensity: str = Form(...)):

    workout_plan = get_ai_response("Create workout plan")
    nutrition_tip = get_ai_response("Give nutrition tip")

    if not workout_plan:
        workout_plan = "Sample workout plan"

    if not nutrition_tip:
        nutrition_tip = "Eat balanced meals."

    conn = sqlite3.connect('fitness.db')
    c = conn.cursor()
    c.execute('INSERT INTO users (name, age, weight, goal, intensity, workout_plan, nutrition_tip) VALUES (?,?,?,?,?,?,?)',
              (name, age, weight, goal, intensity, workout_plan, nutrition_tip))
    user_id = c.lastrowid
    conn.commit()
    conn.close()

    return templates.TemplateResponse("result.html", {
        "request": request,
        "name": name,
        "workout_plan": workout_plan,
        "nutrition_tip": nutrition_tip,
        "user_id": user_id,
        "goal": goal,
        "intensity": intensity
    })

@app.post("/feedback/{user_id}")
def feedback(request: Request, user_id: int, feedback: str = Form(...)):

    conn = sqlite3.connect('fitness.db')
    c = conn.cursor()
    c.execute('SELECT workout_plan,name FROM users WHERE id=?',(user_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        return HTMLResponse("User not found", status_code=404)

    updated_plan = get_ai_response("Update workout plan")

    if not updated_plan:
        updated_plan = row[0]

    return templates.TemplateResponse("feedback.html", {
        "request": request,
        "name": row[1],
        "updated_plan": updated_plan,
        "feedback": feedback,
        "user_id": user_id
    })

@app.get("/api/nutrition-tip")
def api_nutrition_tip(goal: str):
    tip = get_ai_response("nutrition tip")
    if not tip:
        tip = "Stay hydrated and eat whole foods."
    return {"goal": goal, "tip": tip}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
