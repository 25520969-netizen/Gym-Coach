# Smart Gym Coach

A workout generator that builds a session for a given time budget while respecting muscle recovery. It is a FastAPI backend with a built-in single-page UI, using MongoDB Atlas to remember what you trained.

## Features

- **Two generation modes**
  - **Standard** (`/api/generate-standard`): controlled randomness. Picks exercises from the safe muscle groups, shuffles them, and fills the time budget.
  - **Smart** (`/api/generate-smart`): a 0/1 knapsack dynamic program that maximizes the total `efficiency` score of the chosen exercises within the time limit (`O(n * T)`).
- **Recovery-aware safety filter.** A muscle group is skipped if it has not rested long enough (24-72 h depending on the group) or has already been trained twice in the last 7 days.
- **Max-heap prioritisation.** Muscle groups are ranked by priority, weekly quota left and hours rested; the final workout is ordered with compound lifts first.
- **No junk volume.** Large muscles get one compound and one isolation exercise, small muscles get one exercise.
- **Exercise swap.** `/api/swap-exercise` runs a breadth-first search over a graph of substitute exercises and returns an alternative.
- **Instant search.** A prefix tree (trie) gives autocomplete over exercise names in `O(m)` for a prefix of length `m`.
- **History.** Completed workouts and single exercises are stored in MongoDB and aggregated into weekly hit counts per muscle target.

## Data

- 58 exercises in `exercises.json` (23 push, 19 pull, 16 legs), each with target muscle, secondary muscles, duration, efficiency score, compound/isolation type, substitutes and a form description.
- 19 muscle targets with group, priority, size and rest hours in `history_manager.py`.

## Project layout

| File | Purpose |
| --- | --- |
| `api.py` | FastAPI app, REST endpoints, and the single-page UI served at `/` |
| `generator.py` | Workout generation (standard and knapsack modes), max-heap, queue, exercise graph with BFS |
| `GymApp.py` | Exercise loading and the trie used for search |
| `history_manager.py` | MongoDB access and weekly aggregation of training history |
| `exercises.json` | Exercise database |

## API

| Method | Path | Description |
| --- | --- | --- |
| GET | `/` | Web UI |
| GET | `/api/generate-standard` | Generate a workout (standard mode) |
| GET | `/api/generate-smart` | Generate a workout (knapsack mode) |
| POST | `/api/complete-workout` | Save a full workout to history |
| POST | `/api/complete-exercise` | Save a single exercise to history |
| GET | `/api/history` | Weekly training summary per muscle target |
| GET | `/api/search` | Prefix search over exercise names |
| GET | `/api/swap-exercise` | Get a substitute for an exercise |

Interactive docs are available at `/docs` once the server is running.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Optional: enable workout history (MongoDB Atlas or any MongoDB)
export MONGO_URI="mongodb+srv://<user>:<password>@<cluster>/?appName=<app>"

uvicorn api:app --reload
```

Open http://localhost:8000. If `MONGO_URI` is not set, the app still runs but does not load or save training history.

## Tech

Python, FastAPI, Uvicorn, PyMongo, MongoDB Atlas, vanilla JavaScript.
