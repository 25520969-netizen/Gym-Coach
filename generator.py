import time
from datetime import datetime
from GymApp import ExerciseManager
from history_manager import HistoryManager, MUSCLE_INFO

# ==========================================
# 1. MAX-HEAP
# ==========================================
class MaxHeap:
    def __init__(self): self.heap = []
    def is_empty(self): return len(self.heap) == 0
    def push(self, item):
        self.heap.append(item)
        self._heapify_up(len(self.heap) - 1)
    def pop(self):
        if self.is_empty(): return None
        if len(self.heap) == 1: return self.heap.pop()
        max_item = self.heap[0]
        self.heap[0] = self.heap.pop()
        self._heapify_down(0)
        return max_item
    def _heapify_up(self, index):
        parent = (index - 1) // 2
        if index > 0 and self.heap[index] > self.heap[parent]:
            self.heap[index], self.heap[parent] = self.heap[parent], self.heap[index]
            self._heapify_up(parent)
    def _heapify_down(self, index):
        largest = index
        left, right = 2 * index + 1, 2 * index + 2
        if left < len(self.heap) and self.heap[left] > self.heap[largest]: largest = left
        if right < len(self.heap) and self.heap[right] > self.heap[largest]: largest = right
        if largest != index:
            self.heap[index], self.heap[largest] = self.heap[largest], self.heap[index]
            self._heapify_down(largest)

# ==========================================
# 2. CẤU TRÚC HÀNG ĐỢI (QUEUE) & ĐỒ THỊ (GRAPH)
# ==========================================
class Node:
    def __init__(self, value):
        self.value = value
        self.next = None

class CustomQueue:
    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0

    def is_empty(self):
        return self.size == 0

    def enqueue(self, value):
        new_node = Node(value)
        if self.tail is None:
            self.head = self.tail = new_node
        else:
            self.tail.next = new_node
            self.tail = new_node
        self.size += 1

    def dequeue(self): 
        if self.is_empty():
            return None
        temp = self.head
        self.head = temp.next
        if self.head is None:
            self.tail = None
        self.size -= 1
        return temp.value

class ExerciseGraph:
    def __init__(self, exercises):
        self.adj_list = {}
        self.exercise_map = {ex['id']: ex for ex in exercises}
        self.build_graph(exercises)

    def build_graph(self, exercises):
        for ex in exercises:
            ex_id = ex['id']
            if ex_id not in self.adj_list:
                self.adj_list[ex_id] = []
            
            for sub_id in ex.get('substitutes', []):
                if sub_id not in self.adj_list: 
                    self.adj_list[sub_id] = []
                
                if sub_id not in self.adj_list[ex_id]:
                    self.adj_list[ex_id].append(sub_id)
                if ex_id not in self.adj_list[sub_id]:
                    self.adj_list[sub_id].append(ex_id)

    def find_substitute_bfs(self, start_id):
        visited = set()
        queue = CustomQueue()
        
        queue.enqueue(start_id)
        visited.add(start_id)

        while not queue.is_empty():
            current_id = queue.dequeue()
            
            # Quét các bài tập lân cận
            for neighbor_id in self.adj_list.get(current_id, []):
                if neighbor_id not in visited:
                    return self.exercise_map[neighbor_id]
        
        return None # Không tìm thấy bài nào để đổi

# ==========================================
# 3. RANDOM
# ==========================================
class CustomRandom:
    def __init__(self, seed=None):
        self.state = int(time.time() * 1000) if seed is None else seed
        self.a, self.c, self.m = 1103515245, 12345, 2**31
    def random(self):
        self.state = (self.a * self.state + self.c) % self.m
        return self.state / self.m
    def randint(self, min_val, max_val):
        return min_val + int(self.random() * (max_val - min_val + 1))
    def choice(self, array):
        return array[self.randint(0, len(array) - 1)] if array else None
    def shuffle(self, array):
        n = len(array)
        for i in range(n - 1, 0, -1):
            j = self.randint(0, i)
            array[i], array[j] = array[j], array[i]

# ==========================================
# 4. WORKOUT GENERATOR
# ==========================================
class WorkoutGenerator:
    def __init__(self, manager: ExerciseManager, history_manager: HistoryManager):
        self.manager = manager
        self.history_manager = history_manager
        self.rng = CustomRandom() 
        self.templates = {
            "PUSH": ["UPPER_CHEST", "MID_CHEST", "CHEST_FLY", "FRONT_DELT", "LATERAL_DELT", "TRICEP_LATERAL", "TRICEP_LONG"],
            "PULL": ["BACK_VERTICAL", "BACK_HORIZONTAL", "BACK_ISOLATION", "BICEP_LONG", "BICEP_SHORT_BRAC", "REAR_DELT"],
            "LEG":  ["QUAD_PRIMARY", "HAMSTRING_PRIMARY", "QUAD_SECONDARY", "QUAD_ISOLATION", "HAMSTRING_ISOLATION", "CALF_ISOLATION"]
        }

    # --- HÀM BẢO VỆ CỐT LÕI (GLOBAL SAFETY FILTER) ---
    def _get_safe_targets(self, day_type):
        """Lọc ra các nhóm cơ an toàn (Đủ giờ nghỉ, Chưa vượt quota tuần)"""
        history_data = self.history_manager.history
        now = datetime.now()
        safe_targets = []
        pq = MaxHeap()

        # Nếu chọn PUSH/PULL/LEG, chỉ kiểm tra các cơ trong ngày đó. Nếu AUTO, kiểm tra toàn thân.
        candidate_targets = self.templates.get(day_type, MUSCLE_INFO.keys())

        for target in candidate_targets:
            info = MUSCLE_INFO[target]
            hist = history_data.get(target, {})
            
            # 1. Kiểm tra thời gian nghỉ
            if "last_trained_timestamp" in hist and hist["last_trained_timestamp"]:
                last_trained = datetime.fromisoformat(hist["last_trained_timestamp"])
                hours_rested = (now - last_trained).total_seconds() / 3600
                if hours_rested < info["rest_hours"]:
                    continue # Bỏ qua vì chưa nghỉ đủ
            else:
                hours_rested = 168 # Chưa tập bao giờ
            
            # 2. Kiểm tra Quota tuần
            hits = hist.get("hits_this_week", 0)
            if hits >= 2:
                continue # Bỏ qua vì đã đạt KPI
                
            # Chấm điểm Heuristic để xếp hạng nếu là AUTO
            score = info["priority"] * 10 + (2 - hits) * 50 + min(hours_rested, 168)
            pq.push((score, target))
            
        # Lấy tối đa 6 nhóm cơ khát nhất (hoặc lấy tất cả nếu là PPL)
        limit = 6 if day_type == "AUTO" else len(candidate_targets)
        while not pq.is_empty() and len(safe_targets) < limit:
            safe_targets.append(pq.pop()[1])
            
        return safe_targets

    # --- HÀM LỌC CHỐNG JUNK VOLUME ---
    def _build_structured_pool(self, safe_targets):
        """Giới hạn số bài tập: Cơ lớn (1 Comp + 1 Iso), Cơ nhỏ (1 bài)"""
        pool = []
        for target in safe_targets:
            exs = self.manager.get_by_target_area(target)
            compounds = [ex for ex in exs if ex['type_score'] == 2]
            isolations = [ex for ex in exs if ex['type_score'] == 1]
            size = MUSCLE_INFO.get(target, {}).get("size", "SMALL")

            if size == "LARGE":
                # Cơ lớn: Lấy đúng 1 bài Compound và 1 bài Isolation
                if compounds: pool.append(self.rng.choice(compounds))
                if isolations: pool.append(self.rng.choice(isolations))
            else:
                # Cơ nhỏ: Lấy đúng 1 bài
                if isolations: pool.append(self.rng.choice(isolations))
                elif compounds: pool.append(self.rng.choice(compounds))
        return pool

    # ---------------------------------------------------------
    # CHẾ ĐỘ 1: GEN CHUẨN (Đổi Gió - Ngẫu nhiên có kiểm soát)
    # ---------------------------------------------------------
    def generate_standard_workout(self, day_type, max_time):
        day_type = day_type.upper()
        safe_targets = self._get_safe_targets(day_type)
        if not safe_targets: return []

        # Chỉ lấy các bài tập đã qua phễu lọc chống Junk Volume
        candidate_pool = self._build_structured_pool(safe_targets)
        self.rng.shuffle(candidate_pool)
        
        selected_workout = []
        time_left = max_time

        for ex in candidate_pool:
            duration = ex.get('duration', 10)
            if time_left >= duration:
                selected_workout.append(ex)
                time_left -= duration

        # Đẩy vào MaxHeap để sắp xếp Compound lên đầu
        pq = MaxHeap()
        for ex in selected_workout:
            try: group_idx = safe_targets.index(ex['target_area'])
            except ValueError: group_idx = 99
            pq.push((-group_idx, ex['type_score'], ex['id'], ex))

        final_workout = []
        while not pq.is_empty():
            final_workout.append(pq.pop()[3])

        return self._assign_sets_reps(final_workout)

    # ---------------------------------------------------------
    # CHẾ ĐỘ 2: GEN SMART (Tối ưu DP trên nền tảng an toàn)
    # ---------------------------------------------------------
    def generate_smart_workout(self, day_type, max_time):
        day_type = day_type.upper()
        safe_targets = self._get_safe_targets(day_type)
        if not safe_targets: return []
            
        # Thuật toán DP chỉ được chọn từ danh sách đã bị giới hạn số lượng
        candidate_pool = self._build_structured_pool(safe_targets)
        
        n = len(candidate_pool)
        dp = [[0 for _ in range(max_time + 1)] for _ in range(n + 1)]
        
        # Chạy Bài toán cái túi (Knapsack)
        for i in range(1, n + 1):
            ex = candidate_pool[i-1]
            duration = ex.get('duration', 10)
            val = ex.get('efficiency', 50)
            for w in range(max_time + 1):
                if duration <= w:
                    dp[i][w] = max(val + dp[i-1][w-duration], dp[i-1][w])
                else:
                    dp[i][w] = dp[i-1][w]
                    
        dp_selected = []
        w = max_time
        for i in range(n, 0, -1):
            if dp[i][w] != dp[i-1][w]:
                ex = candidate_pool[i-1]
                dp_selected.append(ex)
                w -= ex.get('duration', 10)
                
        # Sắp xếp bằng Max-Heap
        pq = MaxHeap()
        for ex in dp_selected:
            try: group_idx = safe_targets.index(ex['target_area'])
            except ValueError: group_idx = 99
            pq.push((-group_idx, ex['type_score'], ex['id'], ex))
            
        sorted_workout = []
        while not pq.is_empty():
            sorted_workout.append(pq.pop()[3])
            
        return self._assign_sets_reps(sorted_workout)

    # ==========================================
    # HÀM PHỤ TRỢ: GÁN SETS/REPS THEO LOẠI BÀI TẬP
    # ==========================================
    def _assign_sets_reps(self, workout_list):
        for ex in workout_list:
            if ex.get('type_score') == 2:
                ex['sets'] = "3-4"
                ex['reps'] = "6-10"
            else:
                ex['sets'] = "3"
                ex['reps'] = "10-15"
        return workout_list
                
    