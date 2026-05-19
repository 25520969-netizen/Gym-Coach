import pymongo
from datetime import datetime, timedelta
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
        uri = "mongodb+srv://25520969Kim:42@nhThu@cluster0.xxx.mongodb.net/?retryWrites=true&w=majority"
        
        try:
            self.client = pymongo.MongoClient(uri)
            self.db = self.client["smart_gym_db"]
            self.collection = self.db["workout_history"]
            self.history = self._load_and_aggregate_history()
            print("Đã kết nối MongoDB thành công!")
        except Exception as e:
            print("Cảnh báo: Chưa kết nối được MongoDB.", e)
            self.history = {}

    def record_workout(self, exercises):
        workout_record = {
            "date": datetime.now().isoformat(),
            "exercises": exercises
        }
        try:
            self.collection.insert_one(workout_record)
            self.history = self._load_and_aggregate_history()
        except Exception as e:
            print("Lỗi khi ghi lịch sử vào DB:", e)

    def record_single_exercise(self, exercise):
        workout_record = {
            "date": datetime.now().isoformat(),
            "exercises": [exercise] 
        }
        try:
            self.collection.insert_one(workout_record)
            self.history = self._load_and_aggregate_history()
        except Exception as e:
            print("Lỗi khi ghi lịch sử bài tập đơn vào DB:", e)

    def _load_and_aggregate_history(self):
        aggregated = {}
        one_week_ago = datetime.now() - timedelta(days=7)
        
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
            print("Lỗi khi đọc lịch sử từ DB:", e)
            
        return aggregated