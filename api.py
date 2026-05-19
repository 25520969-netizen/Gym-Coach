from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

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

# Khởi tạo Mạng đồ thị thay thế bài tập (Dùng cho BFS)
exercise_graph = ExerciseGraph(manager.raw_exercises)

# FRONTEND
@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    html_content = """
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Smart Gym Coach</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; padding: 15px; max-width: 600px; margin: auto; background-color: #f0f2f5; color: #1c1e21; }
            h1 { text-align: center; color: #1877f2; font-size: 24px; margin-bottom: 5px;}
            .subtitle { text-align: center; color: #65676b; font-size: 14px; margin-bottom: 20px; }
            
            /* CSS TÌM KIẾM (TRIE) */
            .search-box { position: relative; margin-bottom: 20px; }
            .search-input { width: 100%; padding: 14px 40px 14px 15px; border: 2px solid #1877f2; border-radius: 10px; font-size: 16px; box-sizing: border-box; outline: none; transition: 0.3s; }
            .search-input:focus { box-shadow: 0 0 8px rgba(24,119,242,0.3); }
            .search-results { position: absolute; top: 100%; left: 0; right: 0; background: white; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); max-height: 250px; overflow-y: auto; z-index: 1000; display: none; margin-top: 5px; }
            .search-item { padding: 12px 15px; border-bottom: 1px solid #f0f2f5; cursor: pointer; display: flex; flex-direction: column; }
            .search-item:hover { background-color: #f0f2f5; }
            .search-item b { color: #1c1e21; font-size: 15px; }
            .search-item span { color: #65676b; font-size: 12px; margin-top: 4px; }

            /* CSS THANH TIẾN ĐỘ CƠ BẮP */
            .muscle-dashboard { background: white; padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }
            .progress-row { display: flex; align-items: center; margin-bottom: 12px; }
            .progress-label { width: 85px; font-size: 13px; font-weight: bold; color: #1c1e21; text-align: left; }
            .progress-track { flex: 1; background: #e4e6eb; height: 14px; border-radius: 8px; overflow: hidden; position: relative; margin: 0 10px; }
            .progress-fill { height: 100%; width: 0%; transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1), background-color 0.6s ease; }
            .progress-status { width: 45px; font-size: 12px; font-weight: bold; color: #65676b; text-align: right; }
            
            .control-panel { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); margin-bottom: 20px; }
            .input-group { margin-bottom: 15px; }
            label { display: block; font-weight: bold; margin-bottom: 8px; font-size: 14px;}
            select, input[type="number"] { width: 100%; padding: 12px; border: 1px solid #ccd0d5; border-radius: 8px; font-size: 16px; box-sizing: border-box; background: #f5f6f7;}
            
            .btn-group { display: flex; gap: 10px; margin-top: 15px; }
            button { flex: 1; padding: 14px; font-size: 15px; font-weight: bold; border: none; border-radius: 8px; cursor: pointer; transition: 0.2s; color: white; }
            button:active { transform: scale(0.96); }
            .btn-standard { background-color: #8e44ad; }
            .btn-smart { background-color: #e67e22; }
            .btn-finish { background-color: #27ae60; width: 100%; margin-top: 20px; font-size: 18px; display: none; }
            
            /* CSS ĐỔI BÀI TẬP (GRAPH BFS) */
            .btn-swap { background-color: #f0f2f5; color: #1c1e21; border: 1px solid #ccd0d5; padding: 6px 12px; font-size: 12px; border-radius: 6px; margin-top: 8px; margin-left: 10px; font-weight: bold;}
            .btn-swap:hover { background-color: #e4e6eb; }
            
            .card { background: white; padding: 15px; border-radius: 10px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 5px solid #1877f2; position: relative;}
            .card-title { font-size: 16px; font-weight: bold; margin-bottom: 8px; color: #1c1e21; padding-right: 20px;}
            .card-meta { font-size: 13px; color: #65676b; line-height: 1.5; }
            .badge-compound { background: #1c1e21; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; }
            .badge-isolation { background: #828282; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; }
            
            #loading { text-align: center; display: none; font-style: italic; color: #888; padding: 20px;}
            .summary { text-align: center; font-weight: bold; color: #e74c3c; margin-bottom: 15px; font-size: 18px;}
        </style>
    </head>
    <body>

        <h1>Smart Gym Coach</h1>
        <div class="subtitle">Hệ thống tối ưu hóa cơ bắp theo thời gian thực</div>

        <!-- 1. TÍNH NĂNG AUTOCOMPLETE SEARCH (TRIE) -->
        <div class="search-box">
            <input type="text" id="searchInput" class="search-input" placeholder="🔍 Tìm nhanh bài tập (Ví dụ: Press, Squat...)" oninput="handleSearch(this.value)">
            <div id="searchResults" class="search-results"></div>
        </div>

        <!-- 2. BẢN ĐỒ TIẾN ĐỘ CƠ BẮP -->
        <div class="muscle-dashboard">
            <h3 style="margin: 0 0 15px 0; font-size: 16px; color: #1c1e21; text-align: center;">📊 Mức Độ Kích Thích Trong Tuần</h3>
            <div id="progressContainer"></div>
        </div>

        <!-- 3. ĐIỀU KHIỂN -->
        <div class="control-panel">
            <div class="input-group">
                <label>Bạn có bao nhiêu phút hôm nay?</label>
                <input type="number" id="maxTime" value="45" min="15" max="120">
            </div>
            
            <div class="input-group">
                <label>Nhóm cơ mục tiêu:</label>
                <select id="dayType">
                    <option value="AUTO">🤖 AUTO (Tự quét lịch sử & chọn cơ)</option>
                    <option value="PUSH">Đẩy (Ngực, Vai, Tay sau)</option>
                    <option value="PULL">Kéo (Lưng, Tay trước, Vai sau)</option>
                    <option value="LEG">Chân (Đùi, Mông, Bắp chân)</option>
                </select>
            </div>

            <div class="btn-group">
                <button class="btn-standard" onclick="generateWorkout('standard')">Đổi Gió (Chuẩn)</button>
                <button class="btn-smart" onclick="generateWorkout('smart')">Tối Ưu DP</button>
            </div>
        </div>

        <div id="loading">Đang phân tích cơ bắp & xếp lịch...</div>
        <div id="workout-list"></div>
        
        <button id="btnFinish" class="btn-finish" onclick="completeWorkout()">✅ HOÀN THÀNH BUỔI TẬP</button>

        <script>
            let currentWorkoutData = [];

            // ==========================================
            // TÍNH NĂNG 1: SEARCH VỚI TRIE
            // ==========================================
            async function handleSearch(query) {
                const resultsBox = document.getElementById('searchResults');
                if (query.trim().length === 0) {
                    resultsBox.style.display = 'none';
                    return;
                }
                
                try {
                    const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
                    const data = await response.json();
                    
                    if (data.results && data.results.length > 0) {
                        resultsBox.innerHTML = '';
                        data.results.forEach(ex => {
                            const item = document.createElement('div');
                            item.className = 'search-item';
                            // Hiển thị tên bài và nhóm cơ để user dễ chọn
                            item.innerHTML = `<b>${ex.name}</b><span>🎯 Nhóm cơ: ${ex.target_area}</span>`;
                            // Khi click vào, hiện popup hướng dẫn tập
                            item.onclick = () => {
                                alert(`HƯỚNG DẪN TẬP:\n${ex.name}\n\n${ex.description || "Đang cập nhật..."}`);
                                resultsBox.style.display = 'none';
                                document.getElementById('searchInput').value = '';
                            };
                            resultsBox.appendChild(item);
                        });
                        resultsBox.style.display = 'block';
                    } else {
                        resultsBox.innerHTML = '<div class="search-item"><span>Không tìm thấy bài tập nào.</span></div>';
                        resultsBox.style.display = 'block';
                    }
                } catch (e) {
                    console.error("Lỗi search: ", e);
                }
            }

            // Đóng hộp search khi click ra ngoài
            document.addEventListener('click', function(event) {
                const searchBox = document.querySelector('.search-box');
                if (!searchBox.contains(event.target)) {
                    document.getElementById('searchResults').style.display = 'none';
                }
            });


            // ==========================================
            // TÍNH NĂNG 2: SWAP EXERCISE VỚI GRAPH BFS
            // ==========================================
            async function swapExercise(index, currentId) {
                const btn = document.getElementById(`swap-btn-${index}`);
                const originalText = btn.innerText;
                btn.innerText = 'Đang tìm...';
                btn.disabled = true;

                try {
                    const response = await fetch(`/api/swap-exercise?current_id=${currentId}`);
                    const data = await response.json();

                    if (data.status === 'success') {
                        // Cập nhật lại mảng data tại đúng vị trí đó
                        currentWorkoutData[index] = data.new_exercise;
                        // Render lại nguyên danh sách
                        renderWorkoutList();
                        alert(`Đã đổi sang bài: ${data.new_exercise.name}`);
                    } else {
                        alert(data.message);
                        btn.innerText = originalText;
                        btn.disabled = false;
                    }
                } catch (error) {
                    alert('Lỗi kết nối khi đổi bài!');
                    btn.innerText = originalText;
                    btn.disabled = false;
                }
            }


            // ==========================================
            // CODE RENDER DANH SÁCH BÀI TẬP & DP
            // ==========================================
            function renderWorkoutList() {
                const listDiv = document.getElementById('workout-list');
                listDiv.innerHTML = '';
                
                let totalTime = 0;
                let totalScore = 0;

                currentWorkoutData.forEach((ex, index) => {
                    totalTime += (ex.duration || 0);
                    totalScore += (ex.efficiency || 0);

                    const badgeClass = ex.type_score === 2 ? 'badge-compound' : 'badge-isolation';
                    const badgeText = ex.type_score === 2 ? 'Compound' : 'Isolation';
                    const secondaryTargets = ex.secondary_targets && ex.secondary_targets.length > 0 
                                             ? `<br>🎯 Cơ phụ: ${ex.secondary_targets.join(', ')}` 
                                             : '';
                    const description = ex.description || "Đang cập nhật hướng dẫn cho bài tập này.";

                    const cardHTML = `
                        <div class="card">
                            <div class="card-title">${index + 1}. ${ex.name}</div>
                            <div class="card-meta">
                                <span class="${badgeClass}">${badgeText}</span> 
                                | Nhóm cơ: <b>${ex.target_area}</b>
                                ${secondaryTargets}
                                
                                <div style="margin-top: 10px; background: #f0f2f5; padding: 8px; border-radius: 6px; text-align: center; border: 1px solid #ddd;">
                                    <span style="font-weight: bold; color: #2c3e50; font-size: 14px;">
                                        🔥 Khuyến nghị: ${ex.sets || 3} Hiệp x ${ex.reps || '8-12'} Reps
                                    </span>
                                </div>

                                <div style="margin-top: 8px; color: #d35400;">
                                    ⏱ ${ex.duration} phút | ⭐ Điểm: ${ex.efficiency}
                                </div>
                                
                                <button onclick="toggleDescription(${index})" style="background: none; border: none; color: #1877f2; font-size: 13px; font-weight: bold; cursor: pointer; padding: 0; margin-top: 8px; display: inline-block;">
                                    📖 Xem cách tập
                                </button>
                                
                                <!-- NÚT ĐỔI BÀI TẬP NẰM Ở ĐÂY -->
                                <button id="swap-btn-${index}" class="btn-swap" onclick="swapExercise(${index}, ${ex.id})">
                                    🔄 Máy bận? Đổi bài
                                </button>

                                <div id="desc-${index}" style="display: none; margin-top: 10px; padding: 12px; background: #e8f4fd; border-radius: 6px; font-size: 13.5px; color: #1c1e21; border-left: 4px solid #1877f2; line-height: 1.5;">
                                    <b>💡 Hướng dẫn chuẩn form:</b><br>
                                    ${description}
                                </div>
                            </div>
                        </div>
                    `;
                    listDiv.innerHTML += cardHTML;
                });
                
                listDiv.innerHTML = `<div class="summary">Tổng thời gian: ${totalTime} phút | Tổng điểm: ${totalScore}</div>` + listDiv.innerHTML;
            }

            async function generateWorkout(mode) {
                const listDiv = document.getElementById('workout-list');
                const loadingDiv = document.getElementById('loading');
                const btnFinish = document.getElementById('btnFinish');
                
                const time = document.getElementById('maxTime').value;
                const day = document.getElementById('dayType').value;
                
                listDiv.innerHTML = ''; 
                btnFinish.style.display = 'none';
                loadingDiv.style.display = 'block'; 

                let apiUrl = mode === 'standard' 
                    ? `/api/generate-standard?day=${day}&time=${time}`
                    : `/api/generate-smart?day=${day}&time=${time}`;

                try {
                    const response = await fetch(apiUrl);
                    const data = await response.json();
                    loadingDiv.style.display = 'none';

                    if (!data.workout || data.workout.length === 0) {
                        listDiv.innerHTML = '<p style="text-align:center; color: red;">Không tìm thấy bài tập phù hợp!</p>';
                        return;
                    }

                    currentWorkoutData = data.workout;
                    renderWorkoutList(); // Gọi hàm render chuyên dụng
                    btnFinish.style.display = 'block';

                } catch (error) {
                    loadingDiv.style.display = 'none';
                    listDiv.innerHTML = '<p style="color:red; text-align:center;">Lỗi kết nối tới Server!</p>';
                }
            }

            // Các hàm còn lại giữ nguyên
            function toggleDescription(index) {
                const descDiv = document.getElementById(`desc-${index}`);
                descDiv.style.display = descDiv.style.display === 'none' ? 'block' : 'none';
            }

            async function completeWorkout() {
                if (currentWorkoutData.length === 0) return;
                const btnFinish = document.getElementById('btnFinish');
                btnFinish.innerText = 'Đang lưu...'; btnFinish.disabled = true;

                try {
                    const response = await fetch('/api/complete-workout', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ exercises: currentWorkoutData })
                    });
                    const result = await response.json();
                    if (result.status === 'success') {
                        alert('🎉 Tuyệt vời! Hệ thống đã ghi nhận lịch sử tập luyện của bạn.');
                        loadMuscleMap(); 
                        document.getElementById('workout-list').innerHTML = '';
                        btnFinish.style.display = 'none';
                        btnFinish.innerText = '✅ HOÀN THÀNH BUỔI TẬP';
                        btnFinish.disabled = false;
                        currentWorkoutData = []; 
                    }
                } catch (error) {
                    alert('Lỗi khi lưu lịch sử. Vui lòng thử lại!');
                    btnFinish.innerText = '✅ HOÀN THÀNH BUỔI TẬP'; btnFinish.disabled = false;
                }
            }

            const displayMuscles = [
                { id: "MID_CHEST", name: "Ngực" }, { id: "BACK_VERTICAL", name: "Lưng xô" },
                { id: "QUAD_PRIMARY", name: "Đùi trước" }, { id: "HAMSTRING_PRIMARY", name: "Đùi sau" },
                { id: "FRONT_DELT", name: "Vai" }, { id: "TRICEP_LATERAL", name: "Tay sau" }
            ];

            async function loadMuscleMap() {
                const container = document.getElementById('progressContainer');
                container.innerHTML = ''; 
                try {
                    const response = await fetch('/api/history');
                    const historyData = await response.json();

                    displayMuscles.forEach(m => {
                        const hits = historyData[m.id] ? historyData[m.id].hits_this_week : 0;
                        let width = '0%', color = '#e4e6eb', text = '0/2';
                        if (hits === 1) { width = '50%'; color = '#a2e9c1'; text = '1/2'; } 
                        else if (hits >= 2) { width = '100%'; color = '#27ae60'; text = '2/2 ✓'; }

                        const rowHTML = `
                            <div class="progress-row">
                                <div class="progress-label">${m.name}</div>
                                <div class="progress-track"><div class="progress-fill" style="width: ${width}; background-color: ${color};"></div></div>
                                <div class="progress-status" style="color: ${hits >= 2 ? '#27ae60' : '#65676b'}">${text}</div>
                            </div>
                        `;
                        container.innerHTML += rowHTML;
                    });
                } catch (error) { console.log("Lỗi tải tiến độ cơ bắp", error); }
            }
            window.onload = loadMuscleMap;
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# API ENDPOINTS

@app.get("/api/generate-standard")
def api_gen_standard(day: str, time: int):
    workout = generator.generate_standard_workout(day, time)
    return {"status": "success", "workout": workout}

@app.get("/api/generate-smart")
def api_gen_smart(day: str, time: int):
    workout = generator.generate_smart_workout(day, time)
    return {"status": "success", "workout": workout}

# Pydantic model for JSON
class WorkoutLog(BaseModel):
    exercises: List[dict]

@app.post("/api/complete-workout")
def api_complete_workout(log: WorkoutLog):
    # Call HistoryManager
    history_manager.record_workout(log.exercises)
    return {"status": "success", "message": "Đã cập nhật lịch sử."}

@app.get("/api/history")
def get_history():
    # Trả về toàn bộ lịch sử để Frontend vẽ bản đồ cơ bắp
    return history_manager.history

@app.get("/api/search")
def api_search_exercise(q: str):
    """
    API sử dụng cấu trúc Trie để Gợi ý tìm kiếm (Autocomplete).
    Trả về danh sách các bài tập khớp với từ khóa gõ vào.
    """
    if not q:
        return {"status": "success", "results": []}
    
    # manager.search_exercises() chính là hàm bọc bên ngoài trie.search_prefix()
    results = manager.search_exercises(q) 
    return {"status": "success", "results": results}


@app.get("/api/swap-exercise")
def api_swap_exercise(current_id: int):
    """
    API sử dụng thuật toán Duyệt đồ thị (BFS) để tìm bài tập thay thế tương đương.
    """
    # Chạy BFS để quét trên Đồ thị các bài tập
    new_exercise = exercise_graph.find_substitute_bfs(current_id)
    
    if new_exercise:
        return {
            "status": "success", 
            "message": "Đã tìm thấy bài thay thế phù hợp",
            "new_exercise": new_exercise
        }
    else:
        return {
            "status": "fail", 
            "message": "Không tìm thấy bài tập thay thế nào trong CSDL!"
        }