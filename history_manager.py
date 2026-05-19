import pymongo
from datetime import datetime, timedelta
import os

MUSCLE_INFO = {
    "MID_CHEST": {"group": "PUSH", "priority": 1},
    "UPPER_CHEST": {"group": "PUSH", "priority": 2},
    "LOWER_CHEST": {"group": "PUSH", "priority": 3},
    "FRONT_DELT": {"group": "PUSH", "priority": 2},
    "SIDE_DELT": {"group": "PUSH", "priority": 2},
    "TRICEP_LATERAL": {"group": "PUSH", "priority": 2},
    "TRICEP_LONG": {"group": "PUSH", "priority": 2},
    "BACK_VERTICAL": {"group": "PULL", "priority": 1},
    "BACK_HORIZONTAL": {"group": "PULL", "priority": 1},
    "REAR_DELT": {"group": "PULL", "priority": 2},
    "TRAPEZIUS": {"group": "PULL", "priority": 3},
    "BICEP_SHORT": {"group": "PULL", "priority": 2},
    "BICEP_LONG": {"group": "PULL", "priority": 2},
    "FOREARM": {"group": "PULL", "priority": 3},
    "QUAD_PRIMARY": {"group": "LEG", "priority": 1},
    "HAMSTRING_PRIMARY": {"group": "LEG", "priority": 1},
    "GLUTE": {"group": "LEG", "priority": 2},
    "CALF": {"group": "LEG", "priority": 3},
    "ABS": {"group": "CORE", "priority": 1},
    "OBLIQUES": {"group": "CORE", "priority": 2}
}

class HistoryManager:
    def __init__(self, uri_env_var="MONGO_URI"):
        uri = os.getenv(uri_env_var, "") 
        
        try:
            self.client = pymongo.MongoClient(uri)
            self.db = self.client["smart_gym_db"]
            self.collection = self.db["workout_history"]
            self.history = self._load_and_aggregate_history()
            print("Đã kết nối MongoDB thành công!")
        except Exception as e:
            print("Cảnh báo: Chưa kết nối được MongoDB. Vui lòng kiểm tra lại MONGO_URI.", e)
            self.history = {}

    def record_workout(self, exercises):
        """Lưu lịch sử một buổi tập vào MongoDB"""
        workout_record = {
            "date": datetime.now().isoformat(),
            "exercises": exercises
        }
        try:
            self.collection.insert_one(workout_record)
            self.history = self._load_and_aggregate_history()
        except Exception as e:
            print("Lỗi khi ghi lịch sử vào DB:", e)

    def _load_and_aggregate_history(self):
        """Đọc lịch sử từ MongoDB và gom nhóm theo target_area (7 ngày qua)"""
        aggregated = {}
        one_week_ago = datetime.now() - timedelta(days=7)
        
        try:
            # Truy vấn các buổi tập trong 7 ngày gần nhất
            recent_workouts = self.collection.find({
                "date": {"$gte": one_week_ago.isoformat()}
            })

            for workout in recent_workouts:
                for ex in workout.get("exercises", []):
                    target = ex.get("target_area")
                    if target not in aggregated:
                        aggregated[target] = {"hits_this_week": 0}
                    aggregated[target]["hits_this_week"] += 1
        except Exception as e:
            print("Lỗi khi đọc lịch sử từ DB:", e)
            
        return aggregated
    
    def record_single_exercise(self, exercise):
        """Lưu lịch sử một bài tập đơn lẻ ngay khi người dùng bấm hoàn thành"""
        workout_record = {
            "date": datetime.now().isoformat(),
            "exercises": [exercise] 
        }
        try:
            self.collection.insert_one(workout_record)
            self.history = self._load_and_aggregate_history()
        except Exception as e:
            print("Lỗi khi ghi lịch sử bài tập đơn vào DB:", e)