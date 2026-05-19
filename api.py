from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel 

# Import core modules
from GymApp import ExerciseManager
from history_manager import HistoryManager
from generator import WorkoutGenerator, ExerciseGraph

app = FastAPI(title="Smart PPL Coach")
# Cấp quyền truy cập cho thư mục static chứa ảnh
app.mount("/static", StaticFiles(directory="static"), name="static")

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
            
            /* Ẩn nút hoàn thành cũ đi vì giờ dùng nút lẻ */
            .btn-finish { display: none !important; }
            
            /* CSS ĐỔI BÀI TẬP VÀ HOÀN THÀNH LẺ */
            .btn-swap { background-color: #f0f2f5; color: #1c1e21; border: 1px solid #ccd0d5; padding: 6px 12px; font-size: 12px; border-radius: 6px; margin-top: 8px; margin-left: 10px; font-weight: bold;}
            .btn-swap:hover { background-color: #e4e6eb; }
            
            .btn-done-single { background-color: #27ae60; color: white; border: none; padding: 6px 12px; font-size: 12px; border-radius: 6px; margin-top: 8px; font-weight: bold; cursor: pointer; transition: 0.2s;}
            .btn-done-single:hover { background-color: #219653; }
            .btn-disabled { background-color: #95a5a6; cursor: not-allowed; }
            
            .card { background: white; padding: 15px; border-radius: 10px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 5px solid #1877f2; position: relative;}
            .card-title { font-size: 16px; font-weight: bold; margin-bottom: 8px; color: #1c1e21; padding-right: 20px;}
            .card-meta { font-size: 13px; color: #65676b; line-height: 1.5; }
            .badge-compound { background: #1c1e21; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; }
            .badge-isolation { background: #828282; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; }
            
            #loading { text-align: center; display: none; font-style: italic; color: #888; padding: 20px;}
            .summary { text-align: center; font-weight: bold; color: #e74c3c; margin-bottom: 15px; font-size: 18px;}

            /* CSS POPUP ĐỘNG LỰC */
            .motivation-modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 9999; justify-content: center; align-items: center; flex-direction: column; animation: fadeIn 0.3s ease-in-out;}
            .motivation-modal img { max-width: 80%; max-height: 60vh; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); border: 4px solid #f1c40f; animation: popIn 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
            .motivation-text { color: #f1c40f; font-size: 24px; font-weight: bold; margin-top: 15px; text-transform: uppercase; text-shadow: 2px 2px 4px rgba(0,0,0,0.8); animation: slideUp 0.5s ease-out;}

            @keyframes popIn { 0% { transform: scale(0.5); opacity: 0; } 100% { transform: scale(1); opacity: 1; } }
            @keyframes fadeIn { 0% { opacity: 0; } 100% { opacity: 1; } }
            @keyframes slideUp { 0% { transform: translateY(20px); opacity: 0;} 100% { transform: translateY(0); opacity: 1;} }
        </style>
    </head>
    <body>

        <h1>Smart Gym Coach</h1>
        <div class="subtitle">Hệ thống tối ưu hóa cơ bắp theo thời gian thực</div>

        <div class="search-box">
            <input type="text" id="searchInput" class="search-input" placeholder="🔍 Tìm nhanh bài tập (Ví dụ: Press, Squat...)" oninput="handleSearch(this.value)">
            <div id="searchResults" class="search-results"></div>
        </div>

        <div class="muscle-dashboard">
            <h3 style="margin: 0 0 15px 0; font-size: 16px; color: #1c1e21; text-align: center;">📊 Mức Độ Kích Thích Trong Tuần</h3>
            <div id="progressContainer"></div>
        </div>

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

        <div id="motivationModal" class="motivation-modal">
            <img id="motivationImg" src="" alt="Motivation">
            <div class="motivation-text">QUÁ ĐỈNH! TIẾP TỤC NÀO! 🔥</div>
        </div>

        <script>
            let currentWorkoutData = [];

            // Danh sách các ảnh khích lệ từ link online
            const motivationImages = [
                'https://i.pinimg.com/736x/44/87/b3/4487b3e938e15ad8bc052c45f331a12e.jpg',
                'https://i.pinimg.com/1200x/39/4b/3d/394b3d998f4750c43f41012544fe5f91.jpg', 
                'https://i.pinimg.com/1200x/26/31/0c/26310c2790f48ffd7173cc956559919e.jpg'
            ];

            // ==========================================
            // TÍNH NĂNG 1: SEARCH VỚI TRIE
            // ==========================================
            async function loadMuscleMap() {
                const container = document.getElementById('progressContainer');
                container.innerHTML = ''; 
                try {
                    const response = await fetch('/api/history');
                    const historyData = await response.json();

                    // Gom nhóm toàn bộ cơ con để thanh tiến độ không bỏ sót bất kỳ bài tập nào
                    const muscleGroups = [
                        { name: "Ngực", keys: ["UPPER_CHEST", "MID_CHEST", "LOWER_CHEST", "CHEST_FLY"] },
                        { name: "Lưng xô", keys: ["BACK_VERTICAL", "BACK_HORIZONTAL", "BACK_ISOLATION"] },
                        { name: "Đùi trước", keys: ["QUAD_PRIMARY", "QUAD_SECONDARY", "QUAD_ISOLATION"] },
                        { name: "Đùi sau", keys: ["HAMSTRING_PRIMARY", "HAMSTRING_ISOLATION", "GLUTE"] },
                        { name: "Vai", keys: ["FRONT_DELT", "LATERAL_DELT", "REAR_DELT"] },
                        { name: "Tay", keys: ["TRICEP_LATERAL", "TRICEP_LONG", "BICEP_LONG", "BICEP_SHORT_BRAC"] }
                    ];

                    muscleGroups.forEach(group => {
                        let hits = 0;
                        // Quét xem trong tuần này anh đã tập bất kỳ cơ con nào thuộc nhóm này chưa
                        group.keys.forEach(k => {
                            if (historyData[k]) hits += historyData[k].hits_this_week;
                        });

                        let width = '0%', color = '#e4e6eb', text = '0/2';
                        if (hits === 1) { width = '50%'; color = '#a2e9c1'; text = '1/2'; } 
                        else if (hits >= 2) { width = '100%'; color = '#27ae60'; text = '2/2 ✓'; }

                        const rowHTML = `
                            <div class="progress-row">
                                <div class="progress-label">${group.name}</div>
                                <div class="progress-track"><div class="progress-fill" style="width: ${width}; background-color: ${color};"></div></div>
                                <div class="progress-status" style="color: ${hits >= 2 ? '#27ae60' : '#65676b'}">${text}</div>
                            </div>
                        `;
                        container.innerHTML += rowHTML;
                    });
                } catch (error) { console.log("Lỗi tải tiến độ cơ bắp", error); }
            }

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
                        currentWorkoutData[index] = data.new_exercise;
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
            // TÍNH NĂNG 3: HOÀN THÀNH TỪNG BÀI LẺ VÀ HIỆN POPUP
            // ==========================================
            async function completeSingleExercise(index) {
                const ex = currentWorkoutData[index];
                const btn = document.getElementById(`complete-btn-${index}`);
                
                // Đổi trạng thái UI ngay lập tức
                btn.innerText = '⏳ Đang lưu...';
                btn.disabled = true;
                btn.classList.add('btn-disabled');

                try {
                    const response = await fetch('/api/complete-exercise', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ exercise: ex })
                    });
                    
                    const result = await response.json();
                    if (result.status === 'success') {
                        btn.innerText = '💪 Đã Xong';
                        
                        // Cập nhật lại bản đồ cơ bắp ngay lập tức
                        loadMuscleMap(); 
                        
                        // Hiển thị ảnh khích lệ
                        showMotivationPopup();
                    }
                } catch (error) {
                    alert('Lỗi kết nối. Hãy thử lại!');
                    btn.innerText = '✅ Xong bài này';
                    btn.disabled = false;
                    btn.classList.remove('btn-disabled');
                }
            }

            function showMotivationPopup() {
                const modal = document.getElementById('motivationModal');
                const img = document.getElementById('motivationImg');
                
                // Chọn ngẫu nhiên 1 bức ảnh trong mảng
                const randomImg = motivationImages[Math.floor(Math.random() * motivationImages.length)];
                img.src = randomImg;
                
                modal.style.display = 'flex';
                
                // Tự động tắt popup sau 2.5 giây
                setTimeout(() => {
                    modal.style.display = 'none';
                }, 2500);
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
                                
                                <button id="complete-btn-${index}" class="btn-done-single" onclick="completeSingleExercise(${index})">
                                    ✅ Xong bài này
                                </button>
                                
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
                
                const time = document.getElementById('maxTime').value;
                const day = document.getElementById('dayType').value;
                
                listDiv.innerHTML = ''; 
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
                    renderWorkoutList(); 

                } catch (error) {
                    loadingDiv.style.display = 'none';
                    listDiv.innerHTML = '<p style="color:red; text-align:center;">Lỗi kết nối tới Server!</p>';
                }
            }

            function toggleDescription(index) {
                const descDiv = document.getElementById(`desc-${index}`);
                descDiv.style.display = descDiv.style.display === 'none' ? 'block' : 'none';
            }

            // Hàm cũ, em vẫn giữ lại nhưng nút ở HTML đã bị ẩn đi bằng CSS rồi
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

class SingleExerciseRequest(BaseModel):
    exercise: dict

@app.post("/api/complete-workout")
def api_complete_workout(log: WorkoutLog):
    # Call HistoryManager
    history_manager.record_workout(log.exercises)
    return {"status": "success", "message": "Đã cập nhật lịch sử."}

@app.post("/api/complete-exercise")
def api_complete_exercise(req: SingleExerciseRequest):
    """API ghi nhận hoàn thành 1 bài tập đơn lẻ"""
    history_manager.record_single_exercise(req.exercise)
    return {"status": "success", "message": "Đã lưu bài tập"}

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