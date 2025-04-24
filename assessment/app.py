from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

DATA_FILE = 'user_progress.json'

@app.route('/')
def h():
    return render_template("index.html")


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

def merge_intervals(intervals):
    if not intervals:
        return []
    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]
    for current in intervals[1:]:
        last = merged[-1]
        if current[0] <= last[1]:
            last[1] = max(last[1], current[1])
        else:
            merged.append(current)
    return merged

def calculate_progress(segments, duration):
    total = sum(end - start for start, end in segments)
    return round(min(100, (total / duration) * 100), 2)

@app.route('/save-progress', methods=['POST'])
def save_progress():
    data = request.json
    user_id = data['user_id']
    new_segments = data['segments']
    duration = data['duration']

    db = load_data()
    user_data = db.get(user_id, {'segments': [], 'last_position': 0, 'duration': duration})

    all_segments = user_data['segments'] + new_segments
    merged_segments = merge_intervals(all_segments)

    user_data['segments'] = merged_segments
    user_data['last_position'] = data['last_position']
    user_data['duration'] = duration
    user_data['progress'] = calculate_progress(merged_segments, duration)

    db[user_id] = user_data
    save_data(db)

    return jsonify({ 'status': 'success', 'progress': user_data['progress'] })

@app.route('/get-progress/<user_id>', methods=['GET'])
def get_progress(user_id):
    db = load_data()
    user_data = db.get(user_id)
    if user_data:
        return jsonify({
            'segments': user_data['segments'],
            'last_position': user_data['last_position'],
            'progress': user_data['progress'],
            'duration': user_data['duration']
        })
    else:
        return jsonify({
            'segments': [],
            'last_position': 0,
            'progress': 0,
            'duration': 1
        })


if __name__ == '__main__':
app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
