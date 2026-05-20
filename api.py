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
            
            /* CSS BẢNG THÀNH TÍCH (THAY THẾ THANH TIẾN ĐỘ CŨ) */
            .achievement-board { background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%); padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 20px; border: 1px solid #e4e6eb; }
            .achievement-title { text-align: center; color: #d35400; font-size: 18px; font-weight: bold; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 1px;}
            .achievement-list { display: flex; flex-direction: column; gap: 10px; }
            .achievement-item { background: white; padding: 12px 15px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.02); border-left: 4px solid #27ae60; display: flex; justify-content: space-between; align-items: center; font-size: 14px; font-weight: bold; color: #2c3e50; transition: transform 0.2s;}
            .achievement-item:hover { transform: translateX(5px); }
            .achievement-item .hits { background: #e8f8f5; color: #27ae60; padding: 5px 12px; border-radius: 20px; font-size: 13px; font-weight: 800;}
            .achievement-empty { text-align: center; color: #7f8c8d; font-size: 14px; font-style: italic; padding: 10px 0;}

            /* BẢNG ĐIỀU KHIỂN */
            .control-panel { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); margin-bottom: 20px; }
            .input-group { margin-bottom: 15px; }
            label { display: block; font-weight: bold; margin-bottom: 8px; font-size: 14px;}
            select, input[type="number"] { width: 100%; padding: 12px; border: 1px solid #ccd0d5; border-radius: 8px; font-size: 16px; box-sizing: border-box; background: #f5f6f7;}
            
            .btn-group { display: flex; gap: 10px; margin-top: 15px; }
            button { flex: 1; padding: 14px; font-size: 15px; font-weight: bold; border: none; border-radius: 8px; cursor: pointer; transition: 0.2s; color: white; }
            button:active { transform: scale(0.96); }
            .btn-standard { background-color: #8e44ad; }
            .btn-smart { background-color: #e67e22; }
            
            /* NÚT HOÀN THÀNH TỔNG */
            .btn-finish { 
                display: none; 
                width: 100%; 
                background-color: #27ae60; 
                color: white; 
                padding: 15px; 
                font-size: 16px; 
                font-weight: bold; 
                border: none; 
                border-radius: 8px; 
                cursor: pointer; 
                margin-top: 20px;
                transition: 0.2s;
            }
            .btn-finish:hover { background-color: #219653; }

            /* CSS ĐỔI BÀI TẬP VÀ HOÀN THÀNH LẺ */
            .btn-swap { background-color: #f0f2f5; color: #1c1e21; border: 1px solid #ccd0d5; padding: 6px 12px; font-size: 12px; border-radius: 6px; margin-top: 8px; margin-left: 10px; font-weight: bold;}
            .btn-swap:hover { background-color: #e4e6eb; }
            
            .btn-done-single { background-color: #27ae60; color: white; border: none; padding: 6px 12px; font-size: 12px; border-radius: 6px; margin-top: 8px; font-weight: bold; cursor: pointer; transition: 0.2s;}
            .btn-done-single:hover { background-color: #219653; }
            .btn-disabled { background-color: #95a5a6; cursor: not-allowed; }
            
            /* CSS DANH SÁCH BÀI TẬP */
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

        <div id="achievementBoard" class="achievement-board">
            <div class="achievement-title">🏆 Các nhóm cơ đã tập</div>
            <div id="achievementList" class="achievement-list">
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

            const motivationImages = [
                'https://i.pinimg.com/736x/44/87/b3/4487b3e938e15ad8bc052c45f331a12e.jpg',
                'https://i.pinimg.com/1200x/39/4b/3d/394b3d998f4750c43f41012544fe5f91.jpg', 
                'https://i.pinimg.com/1200x/26/31/0c/26310c2790f48ffd7173cc956559919e.jpg'
            ];

            // Từ điển dịch key tiếng Anh sang tên Tiếng Việt thân thiện
            const muscleNameMap = {
                "UPPER_CHEST": "Ngực trên", "MID_CHEST": "Ngực giữa", "CHEST_FLY": "Ngực (Bài ép)",
                "FRONT_DELT": "Vai trước", "LATERAL_DELT": "Vai giữa", "REAR_DELT": "Vai sau",
                "TRICEP_LATERAL": "Tay sau (Nhánh ngoài)", "TRICEP_LONG": "Tay sau (Nhánh dài)",
                "BACK_VERTICAL": "Lưng xô (Kéo dọc)", "BACK_HORIZONTAL": "Lưng xô (Kéo ngang)", 
                "BACK_ISOLATION": "Lưng xô (Cô lập)", "TRAPEZIUS": "Cầu vai",
                "BICEP_LONG": "Tay trước (Nhánh dài)", "BICEP_SHORT_BRAC": "Tay trước (Nhánh ngắn)",
                "FOREARM": "Cẳng tay",
                "QUAD_PRIMARY": "Đùi trước (Chính)", "HAMSTRING_PRIMARY": "Đùi sau (Chính)",
                "QUAD_SECONDARY": "Đùi trước (Phụ)", "QUAD_ISOLATION": "Đùi trước (Cô lập)",
                "HAMSTRING_ISOLATION": "Đùi sau (Cô lập)", "GLUTE": "Mông", "CALF_ISOLATION": "Bắp chân",
                "ABS": "Bụng", "OBLIQUES": "Cơ liên sườn"
            };

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
                            item.innerHTML = `<b>${ex.name}</b><span>🎯 Nhóm cơ: ${ex.target_area}</span>`;
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

            document.addEventListener('click', function(event) {
                const searchBox = document.querySelector('.search-box');
                if (!searchBox.contains(event.target)) {
                    document.getElementById('searchResults').style.display = 'none';
                }
            });

            // ==========================================
            // TÍNH NĂNG 2: BẢNG THÀNH TÍCH (LẤY TỪ DB)
            // ==========================================
            async function loadAchievements() {
                const container = document.getElementById('achievementList');
                container.innerHTML = '<div class="achievement-empty">Đang tải dữ liệu...</div>'; 
                try {
                    // Thêm cache-busting timestamp để ép trình duyệt tải mới
                    const response = await fetch(`/api/history?t=${new Date().getTime()}`);
                    const historyData = await response.json();

                    container.innerHTML = ''; 
                    let hasHistory = false;
                    
                    // Lọc qua lịch sử, nhóm cơ nào có số lần tập > 0 thì in ra màn hình
                    for (const [key, data] of Object.entries(historyData)) {
                        if (data.hits_this_week > 0) {
                            hasHistory = true;
                            const friendlyName = muscleNameMap[key] || key;
                            const itemHTML = `
                                <div class="achievement-item">
                                    <span>🔥 Cơ ${friendlyName}</span>
                                    <span class="hits">${data.hits_this_week} bài</span>
                                </div>
                            `;
                            container.innerHTML += itemHTML;
                        }
                    }

                    if (!hasHistory) {
                        container.innerHTML = '<div class="achievement-empty">Bảng thành tích đang trống. Hãy bắt đầu buổi tập ngay! 🏋️‍♂️</div>';
                    }

                } catch (error) { 
                    console.log("Lỗi tải lịch sử", error); 
                    container.innerHTML = '<div class="achievement-empty">Lỗi kết nối CSDL!</div>';
                }
            }


            // ==========================================
            // TÍNH NĂNG 3: SWAP EXERCISE VỚI GRAPH BFS
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
            // TÍNH NĂNG 4: HOÀN THÀNH LẺ VÀ POPUP
            // ==========================================
            async function completeSingleExercise(index) {
                const ex = currentWorkoutData[index];
                const btn = document.getElementById(`complete-btn-${index}`);
                
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
                        loadAchievements(); // Cập nhật lại Bảng Thành Tích lập tức
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
                const randomImg = motivationImages[Math.floor(Math.random() * motivationImages.length)];
                img.src = randomImg;
                modal.style.display = 'flex';
                setTimeout(() => {
                    modal.style.display = 'none';
                }, 2500);
            }

            // ==========================================
            // RENDER BÀI TẬP (GIỮ NGUYÊN HOÀN TOÀN TỪ CODE ANH)
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
                const btnFinish = document.getElementById('btnFinish');
                
                const time = document.getElementById('maxTime').value;
                const day = document.getElementById('dayType').value;
                
                listDiv.innerHTML = ''; 
                loadingDiv.style.display = 'block'; 
                btnFinish.style.display = 'none';

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
                    btnFinish.style.display = 'block';

                } catch (error) {
                    loadingDiv.style.display = 'none';
                    listDiv.innerHTML = '<p style="color:red; text-align:center;">Lỗi kết nối tới Server!</p>';
                }
            }

            function toggleDescription(index) {
                const descDiv = document.getElementById(`desc-${index}`);
                descDiv.style.display = descDiv.style.display === 'none' ? 'block' : 'none';
            }

            // ==========================================
            // HÀM CHỐT CA (CHỈ DỌN DẸP UI, KHÔNG GỌI DB)
            // ==========================================
            async function completeWorkout() {
                if (currentWorkoutData.length === 0) return;
                
                alert('🎉 Tuyệt vời! Anh đã hoàn thành xuất sắc buổi tập hôm nay. Về nghỉ ngơi nạp protein thôi!');
                showMotivationPopup();

                document.getElementById('workout-list').innerHTML = '';
                document.getElementById('btnFinish').style.display = 'none';
                currentWorkoutData = []; 
            }

            // Load Bảng thành tích ngay khi mở web
            window.onload = loadAchievements;
        </script>
    </body>
    </html>
    """
    # GẮN HEADER CHỐNG CACHE VÀO ĐÂY ĐỂ TRÌNH DUYỆT LUÔN LOAD DATA MỚI
    response = HTMLResponse(content=html_content)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# API ENDPOINTS

@app.get("/api/generate-standard")
def api_gen_standard(day: str, time: int):
    workout = generator.generate_standard_workout(day, time)
    return {"status": "success", "workout": workout}

@app.get("/api/generate-smart")
def api_gen_smart(day: str, time: int):
    workout = generator.generate_smart_workout(day, time)
    return {"status": "success", "workout": workout}

class WorkoutLog(BaseModel):
    exercises: List[dict]

class SingleExerciseRequest(BaseModel):
    exercise: dict

@app.post("/api/complete-workout")
def api_complete_workout(log: WorkoutLog):
    history_manager.record_workout(log.exercises)
    return {"status": "success", "message": "Đã cập nhật lịch sử."}

@app.post("/api/complete-exercise")
def api_complete_exercise(req: SingleExerciseRequest):
    history_manager.record_single_exercise(req.exercise)
    return {"status": "success", "message": "Đã lưu bài tập"}

@app.get("/api/history")
def get_history():
    return history_manager._load_and_aggregate_history()

@app.get("/api/search")
def api_search_exercise(q: str):
    if not q:
        return {"status": "success", "results": []}
    
    results = manager.search_exercises(q) 
    return {"status": "success", "results": results}

@app.get("/api/swap-exercise")
def api_swap_exercise(current_id: int):
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