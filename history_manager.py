import pymongo
from datetime import datetime, timedelta
import os

class HistoryManager:
    def __init__(self, uri_env_var="MONGO_URI"):
        # Lấy URI từ biến môi trường (sẽ thiết lập trên Render sau)
        # Tạm thời để một chuỗi rỗng để không báo lỗi khi test local nếu chưa có DB
        uri = os.getenv(uri_env_var, "") 
        
        try:
            # Kết nối tới Cloud MongoDB
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