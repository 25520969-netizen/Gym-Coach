import json

class TrieNode:
    def __init__(self):
        self.children = {}
        self.exercises = []

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, text, exercise):
        text = text.lower()
        node = self.root
        for char in text:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
            
            if exercise not in node.exercises:
                node.exercises.append(exercise)

    def search_prefix(self, prefix):
        prefix = prefix.lower()
        node = self.root
        for char in prefix:
            if char not in node.children:
                return [] 
            node = node.children[char]
        return node.exercises

class ExerciseManager:
    def __init__(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.raw_exercises = data['exercises']
        except FileNotFoundError:
            print(f"Lỗi: Không tìm thấy file {file_path}")
            self.raw_exercises = []

        self.exercise_dict = {}   
        self.target_areas = {}     
        self.graph = {}            
        self.trie = Trie()         

        for ex in self.raw_exercises:
            ex_id = ex['id']
            t_area = ex['target_area']

            self.exercise_dict[ex_id] = ex

            if t_area not in self.target_areas:
                self.target_areas[t_area] = []
            self.target_areas[t_area].append(ex)

            self.graph[ex_id] = ex.get('substitutes', [])

            name = ex['name']
            
            self.trie.insert(name, ex)
            
            words = name.split()
            for i in range(1, len(words)):
                suffix = " ".join(words[i:])
                self.trie.insert(suffix, ex)

    def get_exercise_by_id(self, ex_id):
        return self.exercise_dict.get(ex_id)

    def get_substitutes(self, ex_id):

        sub_ids = self.graph.get(ex_id, [])
        return [self.exercise_dict[sid] for sid in sub_ids if sid in self.exercise_dict]

    def get_by_target_area(self, target_area):
        return self.target_areas.get(target_area, [])

    def search_exercises(self, keyword):
        keyword = keyword.strip()
        if not keyword:
            return []
        return self.trie.search_prefix(keyword)