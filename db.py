import sqlite3
import json
from typing import List, Dict, Any

DB_PATH = 'bot_data.db'

SCHEMA = '''
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS questions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  qid INTEGER,
  subject TEXT,
  question TEXT,
  options TEXT, -- JSON array
  correct_answer INTEGER
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_questions_subject_qid ON questions(subject, qid);

CREATE TABLE IF NOT EXISTS user_activity (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  username TEXT,
  first_name TEXT,
  activity TEXT,
  subject TEXT,
  timestamp TEXT
);
'''


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript(SCHEMA)
    conn.commit()
    conn.close()


def load_questions_from_json(path: str, subject: str):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    inserted = 0
    for q in data:
        qid = q.get('id')
        question = q.get('question')
        options = json.dumps(q.get('options', []), ensure_ascii=False)
        correct = q.get('correct_answer')
        try:
            cur.execute('INSERT OR IGNORE INTO questions (qid, subject, question, options, correct_answer) VALUES (?, ?, ?, ?, ?)',
                        (qid, subject, question, options, correct))
            if cur.rowcount > 0:
                inserted += 1
        except Exception as e:
            print('Error inserting', qid, e)
    conn.commit()
    conn.close()
    return inserted


def get_random_questions(subject: str, n: int) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT qid, question, options, correct_answer FROM questions WHERE subject = ? ORDER BY RANDOM() LIMIT ?', (subject, n))
    rows = cur.fetchall()
    result = []
    for r in rows:
        qid, question, options_json, correct = r
        options = json.loads(options_json)
        result.append({
            'id': qid,
            'question': question,
            'options': options,
            'correct_answer': correct
        })
    conn.close()
    return result


def count_questions(subject: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM questions WHERE subject = ?', (subject,))
    c = cur.fetchone()[0]
    conn.close()
    return c


def log_activity(user_id: int, username: str, first_name: str, activity: str, subject: str = None, timestamp: str = None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('INSERT INTO user_activity (user_id, username, first_name, activity, subject, timestamp) VALUES (?, ?, ?, ?, ?, ?)',
                (user_id, username, first_name, activity, subject, timestamp))
    conn.commit()
    conn.close()


def get_stats_summary():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(DISTINCT user_id) FROM user_activity')
    unique_users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM user_activity WHERE activity = 'test_started'")
    total_tests = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM user_activity WHERE activity = 'test_completed'")
    completed_tests = cur.fetchone()[0]
    cur.execute("SELECT user_id, first_name, username, COUNT(*) as tests FROM user_activity WHERE activity = 'test_started' GROUP BY user_id ORDER BY tests DESC LIMIT 5")
    top = cur.fetchall()
    conn.close()
    return {
        'unique_users': unique_users,
        'total_tests': total_tests,
        'completed_tests': completed_tests,
        'top_users': top
    }
