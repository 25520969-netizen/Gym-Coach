from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel 

# Import core modules
from GymApp import ExerciseManager
from history_manager import HistoryManager
from generator import WorkoutGenerator, ExerciseGraph

app = FastAPI(title="Smart PPL Coach")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Init system brain
manager = ExerciseManager('exercises.json')
history_manager = HistoryManager('history.json')
generator = WorkoutGenerator(manager, history_manager)
exercise_graph = ExerciseGraph(manager.raw_exercises)

@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    html_content = """
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <title>Smart Gym Coach</title>
        <style>
            body { font-family: -apple-system, sans-serif; padding: 15px; max-width: 600px; margin: auto; background-color: #f0f2f5; }
            h1 { text-align: center; color: #1877f2; }
            .control-panel { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }
            .achievement-board { background: #fff; padding: 20px; border-radius: 12px; border: 2px solid #27ae60; margin-bottom: 20px; }
            .achievement-title { text-align: center; color: #27ae60; font-weight: bold; margin-bottom: 10px; }
            .achievement-item { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }
            .card { background: white; padding: 15px; border-radius: 10px; margin-bottom: 12px; border-left: 5px solid #1877f2; }
            .btn-finish { display: none; width: 100%; background-color: #27ae60; color: white; padding: 15px; border: none; border-radius: 8px; cursor: pointer; margin-top: 20px; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>Smart Gym Coach</h1>
        <div class="control-panel">
            <input type="number" id="maxTime" value="45" style="margin-bottom:10px;">
            <select id="dayType">
                <option value="AUTO">🤖 AUTO</option>
                <option value="PUSH">Đẩy</option>
                <option value="PULL">Kéo</option>
                <option value="LEG">Chân</option>
            </select>
            <div style="display:flex; gap:10px; margin-top:10px;">
                <button onclick="generateWorkout('standard')" style="flex:1; background:#8e44ad; padding:10px; border:none; color:white; border-radius:5px;">Đổi Gió</button>
                <button onclick="generateWorkout('smart')" style="flex:1; background:#e67e22; padding:10px; border:none; color:white; border-radius:5px;">Tối Ưu DP</button>
            </div>
        </div>
        <div class="achievement-board">
            <div class="achievement-title">🏆 CÁC NHÓM CƠ ĐÃ TẬP</div>
            <div id="achievementList"></div>
        </div>
        <div id="workout-list"></div>
        <button id="btnFinish" class="btn-finish" onclick="completeWorkout()">✅ CHỐT BUỔI TẬP</button>

        <script>
            let currentWorkoutData = [];
            const muscleNameMap = { "UPPER_CHEST": "Ngực trên", "MID_CHEST": "Ngực giữa", "FRONT_DELT": "Vai trước", "TRICEP_LONG": "Tay sau", "BACK_VERTICAL": "Lưng xô", "QUAD_PRIMARY": "Đùi trước" };

            async function loadAchievements() {
                const list = document.getElementById('achievementList');
                const res = await fetch(`/api/history?t=${new Date().getTime()}`);
                const data = await res.json();
                list.innerHTML = '';
                for (const [key, val] of Object.entries(data)) {
                    if (val.hits_this_week > 0) {
                        list.innerHTML += `<div class="achievement-item"><span>${muscleNameMap[key] || key}</span><b>${val.hits_this_week} buổi</b></div>`;
                    }
                }
            }

            async function generateWorkout(mode) {
                const res = await fetch(`/api/generate-${mode}?day=${document.getElementById('dayType').value}&time=${document.getElementById('maxTime').value}`);
                const data = await res.json();
                currentWorkoutData = data.workout;
                renderWorkoutList();
                document.getElementById('btnFinish').style.display = 'block';
            }

            function renderWorkoutList() {
                const list = document.getElementById('workout-list');
                list.innerHTML = '';
                currentWorkoutData.forEach((ex, i) => {
                    list.innerHTML += `<div class="card"><b>${i+1}. ${ex.name}</b><br>${ex.target_area}<br><button onclick="completeSingleExercise(${i})">✅ Xong</button></div>`;
                });
            }

            async function completeSingleExercise(index) {
                await fetch('/api/complete-exercise', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({exercise: currentWorkoutData[index]})});
                loadAchievements();
                alert("Đã ghi nhận!");
            }

            function completeWorkout() {
                alert('🎉 Chốt buổi tập thành công!');
                document.getElementById('workout-list').innerHTML = '';
                document.getElementById('btnFinish').style.display = 'none';
            }

            window.onload = loadAchievements;
        </script>
    </body>
    </html>
    """
    response = HTMLResponse(content=html_content)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

# API Endpoints giữ nguyên như cũ...
@app.get("/api/generate-standard")
def api_gen_standard(day: str, time: int): return {"workout": generator.generate_standard_workout(day, time)}

@app.get("/api/generate-smart")
def api_gen_smart(day: str, time: int): return {"workout": generator.generate_smart_workout(day, time)}

@app.post("/api/complete-exercise")
def api_complete_exercise(req: SingleExerciseRequest):
    history_manager.record_single_exercise(req.exercise)
    return {"status": "success"}

@app.get("/api/history")
def get_history(): return history_manager.history