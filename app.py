from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import sqlite3

app = Flask(__name__)
CORS(app)

DB_FILE = "reservations.db"

# DB 초기화
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            payment TEXT,
            note TEXT,
            people INTEGER,
            start_time TEXT,
            end_time TEXT,
            seats TEXT
        )
        """)
        conn.commit()

@app.route("/api/reservations", methods=["GET"])
def get_reservations():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reservations")
        rows = cursor.fetchall()
        reservations = [
            {
                "id": row[0],
                "name": row[1],
                "payment": row[2],
                "note": row[3],
                "people": row[4],
                "start": row[5],
                "end": row[6],
                "seats": row[7].split(",")
            } for row in rows
        ]
    return jsonify(reservations)

@app.route("/api/reserve", methods=["POST"])
def reserve():
    data = request.json
    name = data.get("name", "")
    payment = data["payment"]
    note = data.get("note", "")
    people = int(data["people"])
    start_time = datetime.fromisoformat(data["start"])
    end_time = start_time + timedelta(minutes=30)
    seats = data["seats"]

    # 예약 중복 확인
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT start_time, end_time, seats FROM reservations")
        for row in cursor.fetchall():
            exist_start = datetime.fromisoformat(row[0])
            exist_end = datetime.fromisoformat(row[1])
            exist_seats = row[2].split(",")
            if any(seat in exist_seats for seat in seats):
                if (start_time < exist_end and end_time > exist_start):
                    return jsonify({"error": "시간이 겹치는 좌석이 있습니다."}), 409

        cursor.execute("""
            INSERT INTO reservations (name, payment, note, people, start_time, end_time, seats)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, payment, note, people, start_time.isoformat(), end_time.isoformat(), ",".join(seats)))
        conn.commit()

    return jsonify({"message": "예약 완료"})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
