from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt

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
history_manager = HistoryManager('MONGO_URI')
generator = WorkoutGenerator(manager, history_manager)
exercise_graph = ExerciseGraph(manager.raw_exercises)

# ==========================================
# PYDANTIC MODELS (Định nghĩa trước khi dùng)
# ==========================================
class UserAuth(BaseModel):
    username: str
    password: str

class WorkoutLog(BaseModel):
    exercises: List[dict]

class SingleExerciseRequest(BaseModel):
    exercise: dict

# ==========================================
# CẤU HÌNH BẢO MẬT (JWT AUTH)
# ==========================================
SECRET_KEY = "smart_gym_coach_secret_key"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(status_code=401, detail="Không thể xác thực")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception

# ==========================================
# GIAO DIỆN ĐĂNG NHẬP / ĐĂNG KÝ
# ==========================================
@app.get("/login", response_class=HTMLResponse)
def serve_login():
    html_content = """
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Đăng nhập - Smart Gym Coach</title>
        <style>
            body { font-family: -apple-system, sans-serif; background-color: #f0f2f5; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .login-container { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); width: 100%; max-width: 350px; }
            h2 { text-align: center; color: #1877f2; margin-bottom: 25px; }
            input { width: 100%; padding: 12px; margin-bottom: 15px; border: 1px solid #ccd0d5; border-radius: 8px; box-sizing: border-box; font-size: 15px; }
            button { width: 100%; padding: 12px; background-color: #1877f2; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; transition: 0.2s; margin-bottom: 15px; }
            button:hover { background-color: #166fe5; }
            .toggle-btn { background-color: transparent; color: #65676b; border: 1px solid #ccd0d5; width: 100%; padding: 12px; border-radius: 8px; font-weight: bold; cursor: pointer; }
            .toggle-btn:hover { background-color: #f5f6f7; color: #1c1e21; }
            #error-msg { color: #e74c3c; text-align: center; font-size: 14px; margin-bottom: 15px; display: none; font-weight: bold;}
        </style>
    </head>
    <body>
        <div class="login-container">
            <h2 id="form-title">Đăng Nhập</h2>
            <div id="error-msg"></div>
            <input type="text" id="username" placeholder="Tên đăng nhập" autocomplete="off">
            <input type="password" id="password" placeholder="Mật khẩu">
            <button id="main-btn" onclick="handleAuth()">Đăng Nhập</button>
            <button class="toggle-btn" onclick="toggleMode()">Chưa có tài khoản? Đăng ký ngay</button>
        </div>

        <script>
            let isLoginMode = true;

            function toggleMode() {
                isLoginMode = !isLoginMode;
                document.getElementById('form-title').innerText = isLoginMode ? "Đăng Nhập" : "Tạo Tài Khoản";
                document.getElementById('main-btn').innerText = isLoginMode ? "Đăng Nhập" : "Đăng Ký";
                document.querySelector('.toggle-btn').innerText = isLoginMode ? "Chưa có tài khoản? Đăng ký ngay" : "Đã có tài khoản? Đăng nhập";
                document.getElementById('error-msg').style.display = 'none';
            }

            function showError(msg) {
                const errDiv = document.getElementById('error-msg');
                errDiv.innerText = msg;
                errDiv.style.display = 'block';
            }

            async function handleAuth() {
                const user = document.getElementById('username').value.trim();
                const pass = document.getElementById('password').value.trim();
                if (!user || !pass) return showError("Vui lòng nhập đủ thông tin!");

                document.getElementById('main-btn').innerText = "Đang xử lý...";

                try {
                    if (isLoginMode) {
                        const formData = new URLSearchParams();
                        formData.append('username', user);
                        formData.append('password', pass);

                        const res = await fetch('/api/login', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                            body: formData
                        });
                        const data = await res.json();

                        if (res.ok) {
                            localStorage.setItem('gym_token', data.access_token);
                            window.location.href = '/'; 
                        } else {
                            showError(data.detail || "Đăng nhập thất bại");
                        }
                    } else {
                        const res = await fetch('/api/register', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ username: user, password: pass })
                        });
                        const data = await res.json();

                        if (res.ok) {
                            alert("Tạo tài khoản thành công! Vui lòng đăng nhập.");
                            toggleMode();
                        } else {
                            showError(data.detail || "Tên đăng nhập đã tồn tại");
                        }
                    }
                } catch (e) {
                    showError("Lỗi kết nối đến máy chủ.");
                }
                document.getElementById('main-btn').innerText = isLoginMode ? "Đăng Nhập" : "Đăng Ký";
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


# ==========================================
# GIAO DIỆN CHÍNH CỦA ỨNG DỤNG
# ==========================================
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
            
            .header-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
            .logout-btn { background-color: #e74c3c; color: white; border: none; padding: 8px 15px; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 13px;}
            
            .search-box { position: relative; margin-bottom: 20px; }
            .search-input { width: 100%; padding: 14px 40px 14px 15px; border: 2px solid #1877f2; border-radius: 10px; font-size: 16px; box-sizing: border-box; outline: none; }
            .search-results { position: absolute; top: 100%; left: 0; right: 0; background: white; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); max-height: 250px; overflow-y: auto; z-index: 1000; display: none; margin-top: 5px; }
            .search-item { padding: 12px 15px; border-bottom: 1px solid #f0f2f5; cursor: pointer; display: flex; flex-direction: column; }
            .search-item b { color: #1c1e21; font-size: 15px; }
            .search-item span { color: #65676b; font-size: 12px; margin-top: 4px; }
            
            .control-panel { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); margin-bottom: 20px; }
            .input-group { margin-bottom: 15px; }
            label { display: block; font-weight: bold; margin-bottom: 8px; font-size: 14px;}
            select, input[type="number"] { width: 100%; padding: 12px; border: 1px solid #ccd0d5; border-radius: 8px; font-size: 16px; box-sizing: border-box; background: #f5f6f7;}
            
            .btn-group { display: flex; gap: 10px; margin-top: 15px; }
            button { flex: 1; padding: 14px; font-size: 15px; font-weight: bold; border: none; border-radius: 8px; cursor: pointer; color: white; }
            .btn-standard { background-color: #8e44ad; }
            .btn-smart { background-color: #e67e22; }
            
            .achievement-board { background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%); padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 20px; border: 1px solid #e4e6eb; }
            .achievement-title { text-align: center; color: #d35400; font-size: 18px; font-weight: bold; margin-bottom: 15px; text-transform: uppercase; }
            .achievement-list { display: flex; flex-direction: column; gap: 10px; }
            .achievement-item { background: white; padding: 12px 15px; border-radius: 8px; border-left: 4px solid #27ae60; display: flex; justify-content: space-between; align-items: center; font-size: 14px; font-weight: bold; color: #2c3e50; }
            .achievement-item .hits { background: #e8f8f5; color: #27ae60; padding: 5px 12px; border-radius: 20px; font-size: 13px;}
            .achievement-empty { text-align: center; color: #7f8c8d; font-size: 14px; font-style: italic;}

            .btn-finish { display: none; width: 100%; background-color: #27ae60; color: white; padding: 15px; font-size: 16px; font-weight: bold; border: none; border-radius: 8px; cursor: pointer; margin-top: 20px; }
            .btn-swap { background-color: #f0f2f5; color: #1c1e21; border: 1px solid #ccd0d5; padding: 6px 12px; font-size: 12px; border-radius: 6px; margin-top: 8px; margin-left: 10px; font-weight: bold; cursor: pointer; }
            .btn-done-single { background-color: #27ae60; color: white; border: none; padding: 6px 12px; font-size: 12px; border-radius: 6px; margin-top: 8px; font-weight: bold; cursor: pointer;}
            
            .card { background: white; padding: 15px; border-radius: 10px; margin-bottom: 12px; border-left: 5px solid #1877f2; }
            .card-title { font-size: 16px; font-weight: bold; margin-bottom: 8px; color: #1c1e21;}
            .card-meta { font-size: 13px; color: #65676b; line-height: 1.5; }
            .badge-compound { background: #1c1e21; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; }
            .badge-isolation { background: #828282; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; }
            
            #loading { text-align: center; display: none; font-style: italic; color: #888; padding: 20px;}
            .summary { text-align: center; font-weight: bold; color: #e74c3c; margin-bottom: 15px; font-size: 18px;}

            .motivation-modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 9999; justify-content: center; align-items: center; flex-direction: column;}
            .motivation-modal img { max-width: 80%; max-height: 60vh; border-radius: 15px; border: 4px solid #f1c40f; }
            .motivation-text { color: #f1c40f; font-size: 24px; font-weight: bold; margin-top: 15px; text-transform: uppercase; }
        </style>
    </head>
    <body>
        <div class="header-bar">
            <div></div>
            <button class="logout-btn" onclick="logout()">Đăng xuất</button>
        </div>

        <h1>Smart Gym Coach</h1>
        <div class="subtitle">Hệ thống tối ưu hóa cơ bắp theo thời gian thực</div>

        <div class="search-box">
            <input type="text" id="searchInput" class="search-input" placeholder="🔍 Tìm nhanh bài tập..." oninput="handleSearch(this.value)">
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
            <div id="achievementList" class="achievement-list"></div>
        </div>

        <div id="loading">Đang phân tích cơ bắp & xếp lịch...</div>
        <div id="workout-list"></div>
        
        <button id="btnFinish" class="btn-finish" onclick="completeWorkout()">✅ HOÀN THÀNH BUỔI TẬP</button>

        <div id="motivationModal" class="motivation-modal">
            <img id="motivationImg" src="" alt="Motivation">
            <div class="motivation-text">QUÁ ĐỈNH! TIẾP TỤC NÀO! 🔥</div>
        </div>

        <script>
            window.onload = () => {
                if (!localStorage.getItem('gym_token')) {
                    window.location.href = '/login';
                } else {
                    loadAchievements();
                }
            };

            function logout() {
                localStorage.removeItem('gym_token');
                window.location.href = '/login';
            }

            function getAuthHeader() {
                return { 'Authorization': `Bearer ${localStorage.getItem('gym_token')}` };
            }

            let currentWorkoutData = [];
            const motivationImages = [
                'https://i.pinimg.com/736x/44/87/b3/4487b3e938e15ad8bc052c45f331a12e.jpg',
                'https://i.pinimg.com/1200x/39/4b/3d/394b3d998f4750c43f41012544fe5f91.jpg', 
                'https://i.pinimg.com/1200x/26/31/0c/26310c2790f48ffd7173cc956559919e.jpg'
            ];

            const muscleNameMap = {
                "UPPER_CHEST": "Ngực trên", "MID_CHEST": "Ngực giữa", "CHEST_FLY": "Ngực (Bài ép)",
                "FRONT_DELT": "Vai trước", "LATERAL_DELT": "Vai giữa", "REAR_DELT": "Vai sau",
                "TRICEP_LATERAL": "Tay sau ngoài", "TRICEP_LONG": "Tay sau dài",
                "BACK_VERTICAL": "Lưng xô (Dọc)", "BACK_HORIZONTAL": "Lưng xô (Ngang)", 
                "BACK_ISOLATION": "Lưng xô (Cô lập)", "TRAPEZIUS": "Cầu vai",
                "BICEP_LONG": "Tay trước dài", "BICEP_SHORT_BRAC": "Tay trước ngắn",
                "FOREARM": "Cẳng tay",
                "QUAD_PRIMARY": "Đùi trước", "HAMSTRING_PRIMARY": "Đùi sau",
                "GLUTE": "Mông", "CALF_ISOLATION": "Bắp chân", "ABS": "Bụng", "OBLIQUES": "Cơ liên sườn"
            };

            async function handleSearch(query) {
                const resultsBox = document.getElementById('searchResults');
                if (query.trim().length === 0) { resultsBox.style.display = 'none'; return; }
                try {
                    const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
                    const data = await response.json();
                    if (data.results && data.results.length > 0) {
                        resultsBox.innerHTML = '';
                        data.results.forEach(ex => {
                            const item = document.createElement('div');
                            item.className = 'search-item';
                            item.innerHTML = `<b>${ex.name}</b><span>🎯 ${ex.target_area}</span>`;
                            item.onclick = () => {
                                alert(`HƯỚNG DẪN TẬP:\n${ex.name}\n\n${ex.description || "Đang cập nhật..."}`);
                                resultsBox.style.display = 'none';
                                document.getElementById('searchInput').value = '';
                            };
                            resultsBox.appendChild(item);
                        });
                        resultsBox.style.display = 'block';
                    } else {
                        resultsBox.innerHTML = '<div class="search-item"><span>Không tìm thấy bài tập.</span></div>';
                        resultsBox.style.display = 'block';
                    }
                } catch (e) { console.error(e); }
            }

            async function loadAchievements() {
                const container = document.getElementById('achievementList');
                try {
                    const response = await fetch(`/api/history?t=${new Date().getTime()}`, { headers: getAuthHeader() });
                    if (response.status === 401) return logout();
                    
                    const historyData = await response.json();
                    container.innerHTML = ''; 
                    let hasHistory = false;
                    
                    for (const [key, data] of Object.entries(historyData)) {
                        if (data.hits_this_week > 0) {
                            hasHistory = true;
                            container.innerHTML += `<div class="achievement-item"><span>🔥 Cơ ${muscleNameMap[key] || key}</span><span class="hits">${data.hits_this_week} bài</span></div>`;
                        }
                    }
                    if (!hasHistory) container.innerHTML = '<div class="achievement-empty">Bảng thành tích trống. Bắt đầu ngay! 🏋️‍♂️</div>';
                } catch (error) { 
                    container.innerHTML = '<div class="achievement-empty">Lỗi tải dữ liệu.</div>';
                }
            }

            async function swapExercise(index, currentId) {
                const btn = document.getElementById(`swap-btn-${index}`);
                btn.innerText = 'Đang tìm...'; btn.disabled = true;
                try {
                    const response = await fetch(`/api/swap-exercise?current_id=${currentId}`);
                    const data = await response.json();
                    if (data.status === 'success') {
                        currentWorkoutData[index] = data.new_exercise;
                        renderWorkoutList();
                    } else {
                        alert(data.message);
                    }
                } catch (error) { alert('Lỗi kết nối!'); }
                finally { btn.innerText = '🔄 Đổi bài'; btn.disabled = false; }
            }

            async function completeSingleExercise(index) {
                const btn = document.getElementById(`complete-btn-${index}`);
                btn.innerText = '⏳ Đang lưu...'; btn.disabled = true;

                try {
                    const response = await fetch('/api/complete-exercise', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
                        body: JSON.stringify({ exercise: currentWorkoutData[index] })
                    });
                    if (response.status === 401) return logout();
                    
                    if ((await response.json()).status === 'success') {
                        btn.innerText = '💪 Đã Xong';
                        loadAchievements();
                        showMotivationPopup();
                    }
                } catch (error) {
                    alert('Lỗi kết nối!'); btn.innerText = '✅ Xong bài này'; btn.disabled = false;
                }
            }

            function showMotivationPopup() {
                const modal = document.getElementById('motivationModal');
                document.getElementById('motivationImg').src = motivationImages[Math.floor(Math.random() * motivationImages.length)];
                modal.style.display = 'flex';
                setTimeout(() => { modal.style.display = 'none'; }, 2000);
            }

            function renderWorkoutList() {
                const listDiv = document.getElementById('workout-list');
                listDiv.innerHTML = '';
                let totalTime = 0, totalScore = 0;

                currentWorkoutData.forEach((ex, index) => {
                    totalTime += (ex.duration || 0); totalScore += (ex.efficiency || 0);
                    const badgeClass = ex.type_score === 2 ? 'badge-compound' : 'badge-isolation';
                    
                    listDiv.innerHTML += `
                        <div class="card">
                            <div class="card-title">${index + 1}. ${ex.name}</div>
                            <div class="card-meta">
                                <span class="${badgeClass}">${ex.type_score === 2 ? 'Compound' : 'Isolation'}</span> 
                                | Nhóm cơ: <b>${ex.target_area}</b>
                                <div style="margin-top: 10px; background: #f0f2f5; padding: 8px; border-radius: 6px; text-align: center;">
                                    <b>🔥 Khuyến nghị: ${ex.sets || 3} Hiệp x ${ex.reps || '8-12'} Reps</b>
                                </div>
                                <div style="margin-top: 8px; color: #d35400;">⏱ ${ex.duration} phút | ⭐ Điểm: ${ex.efficiency}</div>
                                
                                <button onclick="document.getElementById('desc-${index}').style.display = document.getElementById('desc-${index}').style.display === 'none' ? 'block' : 'none'" style="background: none; border: none; color: #1877f2; font-weight: bold; padding: 0; margin-top: 8px; cursor: pointer;">📖 Xem cách tập</button>
                                <button id="complete-btn-${index}" class="btn-done-single" onclick="completeSingleExercise(${index})">✅ Xong bài này</button>
                                <button id="swap-btn-${index}" class="btn-swap" onclick="swapExercise(${index}, ${ex.id})">🔄 Đổi bài</button>

                                <div id="desc-${index}" style="display: none; margin-top: 10px; padding: 12px; background: #e8f4fd; border-radius: 6px;">
                                    <b>💡 Hướng dẫn:</b><br>${ex.description || "Đang cập nhật..."}
                                </div>
                            </div>
                        </div>`;
                });
                listDiv.innerHTML = `<div class="summary">Tổng thời gian: ${totalTime} phút | Tổng điểm: ${totalScore}</div>` + listDiv.innerHTML;
            }

            async function generateWorkout(mode) {
                const listDiv = document.getElementById('workout-list');
                const loadingDiv = document.getElementById('loading');
                const btnFinish = document.getElementById('btnFinish');
                
                listDiv.innerHTML = ''; loadingDiv.style.display = 'block'; btnFinish.style.display = 'none';

                try {
                    const apiUrl = mode === 'standard' 
                        ? `/api/generate-standard?day=${document.getElementById('dayType').value}&time=${document.getElementById('maxTime').value}`
                        : `/api/generate-smart?day=${document.getElementById('dayType').value}&time=${document.getElementById('maxTime').value}`;
                    
                    const response = await fetch(apiUrl, { headers: getAuthHeader() });
                    if (response.status === 401) return logout();
                    
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

            function completeWorkout() {
                if (currentWorkoutData.length === 0) return;
                alert('🎉 Tuyệt vời! Anh đã hoàn thành xuất sắc buổi tập hôm nay.');
                showMotivationPopup();
                document.getElementById('workout-list').innerHTML = '';
                document.getElementById('btnFinish').style.display = 'none';
                currentWorkoutData = []; 
            }
        </script>
    </body>
    </html>
    """
    response = HTMLResponse(content=html_content)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


# ==========================================
# API ENDPOINTS
# ==========================================
@app.post("/api/register")
def api_register(user: UserAuth):
    success = history_manager.create_user(user.username, user.password)
    if not success:
        raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại")
    return {"message": "Tạo tài khoản thành công!"}

@app.post("/api/login")
def api_login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = history_manager.get_user(form_data.username)
    if not user or not history_manager.verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Sai tài khoản hoặc mật khẩu")
    
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/generate-standard")
def api_gen_standard(day: str, time: int, current_user: str = Depends(get_current_user)):
    workout = generator.generate_standard_workout(day, time, current_user)
    return {"status": "success", "workout": workout[::-1] if workout else []}

@app.get("/api/generate-smart")
def api_gen_smart(day: str, time: int, current_user: str = Depends(get_current_user)):
    workout = generator.generate_smart_workout(day, time, current_user)
    return {"status": "success", "workout": workout[::-1] if workout else []}

@app.post("/api/complete-workout")
def api_complete_workout(log: WorkoutLog, current_user: str = Depends(get_current_user)):
    history_manager.record_workout(current_user, log.exercises)
    return {"status": "success", "message": "Đã cập nhật lịch sử."}

@app.post("/api/complete-exercise")
def api_complete_exercise(req: SingleExerciseRequest, current_user: str = Depends(get_current_user)):
    history_manager.record_single_exercise(current_user, req.exercise)
    return {"status": "success", "message": "Đã lưu bài tập"}

@app.get("/api/history")
def get_history(current_user: str = Depends(get_current_user)):
    return history_manager._load_and_aggregate_history(current_user)

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
        return {"status": "success", "new_exercise": new_exercise}
    return {"status": "fail", "message": "Không tìm thấy bài tập thay thế!"}