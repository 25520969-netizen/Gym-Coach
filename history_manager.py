import pymongo
from datetime import datetime, timedelta
from urllib.parse import quote_plus
import os

MUSCLE_INFO = {
    # Nhóm Đẩy (PUSH)
    "UPPER_CHEST": {"group": "PUSH", "priority": 1, "size": "LARGE", "rest_hours": 48},
    "MID_CHEST": {"group": "PUSH", "priority": 1, "size": "LARGE", "rest_hours": 48},
    "CHEST_FLY": {"group": "PUSH", "priority": 2, "size": "SMALL", "rest_hours": 48},
    "FRONT_DELT": {"group": "PUSH", "priority": 2, "size": "SMALL", "rest_hours": 48},
    "LATERAL_DELT": {"group": "PUSH", "priority": 2, "size": "SMALL", "rest_hours": 48},
    "TRICEP_LATERAL": {"group": "PUSH", "priority": 2, "size": "SMALL", "rest_hours": 48},
    "TRICEP_LONG": {"group": "PUSH", "priority": 2, "size": "SMALL", "rest_hours": 48},
    
    # Nhóm Kéo (PULL)
    "BACK_VERTICAL": {"group": "PULL", "priority": 1, "size": "LARGE", "rest_hours": 48},
    "BACK_HORIZONTAL": {"group": "PULL", "priority": 1, "size": "LARGE", "rest_hours": 48},
    "BACK_ISOLATION": {"group": "PULL", "priority": 2, "size": "SMALL", "rest_hours": 48},
    "BICEP_LONG": {"group": "PULL", "priority": 2, "size": "SMALL", "rest_hours": 48},
    "BICEP_SHORT_BRAC": {"group": "PULL", "priority": 2, "size": "SMALL", "rest_hours": 48},
    "REAR_DELT": {"group": "PULL", "priority": 2, "size": "SMALL", "rest_hours": 48},
    
    # Nhóm Chân (LEG)
    "QUAD_PRIMARY": {"group": "LEG", "priority": 1, "size": "LARGE", "rest_hours": 72},
    "HAMSTRING_PRIMARY": {"group": "LEG", "priority": 1, "size": "LARGE", "rest_hours": 72},
    "QUAD_SECONDARY": {"group": "LEG", "priority": 2, "size": "LARGE", "rest_hours": 72},
    "QUAD_ISOLATION": {"group": "LEG", "priority": 2, "size": "SMALL", "rest_hours": 48},
    "HAMSTRING_ISOLATION": {"group": "LEG", "priority": 2, "size": "SMALL", "rest_hours": 48},
    "CALF_ISOLATION": {"group": "LEG", "priority": 3, "size": "SMALL", "rest_hours": 24}
}

class HistoryManager:
    def __init__(self, uri_env_var="MONGO_URI"):
        self.client = None
        self.db = None
        self.collection = None
        self.history = {} # 👉 Khai báo sẵn biến history để không bao giờ bị sập
        
        username = "25520969Kim"
        password = "42@nhThu"
        host = "cluster0.9ljwfna.mongodb.net"
        
        uri = f"mongodb+srv://{quote_plus(username)}:{quote_plus(password)}@{host}/?appName=Cluster0"
        
        try:
            self.client = pymongo.MongoClient(uri)
            self.db = self.client["smart_gym_db"]
            self.collection = self.db["workout_history"]
            
            # 👉 Nạp dữ liệu vào biến history ngay khi khởi động
            self.history = self._load_and_aggregate_history()
            
            self.client.admin.command('ping')
            print("✅ Đã kết nối MongoDB thành công!", flush=True)
        except Exception as e:
            print("❌ THẤT BẠI: Chưa kết nối được MongoDB. Chi tiết:", e, flush=True)

    def record_workout(self, exercises):
        if self.collection is None: return
        workout_record = {
            "date": datetime.now().isoformat(),
            "exercises": exercises
        }
        try:
            self.collection.insert_one(workout_record)
            # 👉 Cập nhật lại lịch sử sau khi lưu
            self.history = self._load_and_aggregate_history()
        except Exception as e:
            print("Lỗi khi ghi lịch sử vào DB:", e, flush=True)

    def record_single_exercise(self, exercise):
        if self.collection is None: return
        workout_record = {
            "date": datetime.now().isoformat(),
            "exercises": [exercise] 
        }
        try:
            self.collection.insert_one(workout_record)
            # 👉 Cập nhật lại lịch sử sau khi lưu
            self.history = self._load_and_aggregate_history()
        except Exception as e:
            print("Lỗi khi ghi bài tập đơn vào DB:", e, flush=True)

    def _load_and_aggregate_history(self):
        aggregated = {}
        one_week_ago = datetime.now() - timedelta(days=7)
        if self.collection is None: return aggregated
        
        try:
            recent_workouts = self.collection.find({
                "date": {"$gte": one_week_ago.isoformat()}
            }).sort("date", 1)

            for workout in recent_workouts:
                workout_date = workout.get("date")
                for ex in workout.get("exercises", []):
                    target = ex.get("target_area")
                    if target not in aggregated:
                        aggregated[target] = {"hits_this_week": 0, "last_trained_timestamp": workout_date}
                    
                    aggregated[target]["hits_this_week"] += 1
                    aggregated[target]["last_trained_timestamp"] = workout_date
                    
        except Exception as e:
            print("Lỗi khi đọc lịch sử từ DB:", e, flush=True)
            
        return aggregated