import os
import sqlite3
import uuid
import secrets
from datetime import datetime

from flask import Flask, request, jsonify, render_template

DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")
DEFAULT_POINTS = 20
DEFAULT_CREDIT = 80

app = Flask(__name__)


def now_iso():
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nickname TEXT NOT NULL,
            school TEXT,
            tags TEXT,
            credit_score INTEGER NOT NULL,
            points INTEGER NOT NULL,
            activity_points INTEGER NOT NULL,
            token TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS surveys (
            id TEXT PRIMARY KEY,
            owner_id TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            link TEXT NOT NULL,
            reward_points INTEGER NOT NULL,
            deadline TEXT,
            estimated_minutes INTEGER,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS fills (
            id TEXT PRIMARY KEY,
            survey_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            duration_seconds INTEGER,
            status TEXT NOT NULL,
            points_awarded INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS points_logs (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            delta INTEGER NOT NULL,
            reason TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY,
            reporter_id TEXT NOT NULL,
            target_type TEXT NOT NULL,
            target_id TEXT NOT NULL,
            reason TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def error(status, message):
    return jsonify({"error": message}), status


def get_current_user():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth.split(" ", 1)[1].strip()
    if not token:
        return None
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE token = ?", (token,))
    row = cur.fetchone()
    conn.close()
    return row


def require_auth():
    user = get_current_user()
    if not user:
        return None, error(401, "Unauthorized")
    return user, None


def user_response(user_row):
    return {
        "id": user_row["id"],
        "nickname": user_row["nickname"],
        "credit_score": user_row["credit_score"],
        "points": user_row["points"],
        "activity_points": user_row["activity_points"],
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/v1/auth/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    nickname = data.get("nickname", "").strip()
    if not email or not password or not nickname:
        return error(422, "email, password, nickname required")

    user_id = f"u_{uuid.uuid4().hex}"
    token = secrets.token_urlsafe(24)
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO users
                (id, email, password, nickname, school, tags, credit_score,
                 points, activity_points, token, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                email,
                password,
                nickname,
                None,
                None,
                DEFAULT_CREDIT,
                DEFAULT_POINTS,
                0,
                token,
                now_iso(),
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return error(422, "email already registered")
    conn.close()
    return jsonify(
        {
            "access_token": token,
            "expires_in": 3600,
            "user": {"id": user_id, "nickname": nickname},
        }
    )


@app.route("/api/v1/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    if not email or not password:
        return error(422, "email and password required")

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM users WHERE email = ? AND password = ?",
        (email, password),
    )
    user = cur.fetchone()
    if not user:
        conn.close()
        return error(401, "invalid credentials")

    token = secrets.token_urlsafe(24)
    cur.execute("UPDATE users SET token = ? WHERE id = ?", (token, user["id"]))
    conn.commit()
    conn.close()
    return jsonify(
        {
            "access_token": token,
            "expires_in": 3600,
            "user": {"id": user["id"], "nickname": user["nickname"]},
        }
    )


@app.route("/api/v1/users/me", methods=["GET"])
def get_me():
    user, err = require_auth()
    if err:
        return err
    return jsonify(user_response(user))


@app.route("/api/v1/users/me", methods=["PATCH"])
def update_me():
    user, err = require_auth()
    if err:
        return err
    data = request.get_json(silent=True) or {}
    nickname = data.get("nickname", user["nickname"]).strip()
    school = data.get("school", user["school"])
    tags = data.get("tags", user["tags"])
    if isinstance(tags, list):
        tags = ",".join([str(tag).strip() for tag in tags if str(tag).strip()])
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE users SET nickname = ?, school = ?, tags = ?
        WHERE id = ?
        """,
        (nickname, school, tags, user["id"]),
    )
    conn.commit()
    cur.execute("SELECT * FROM users WHERE id = ?", (user["id"],))
    updated = cur.fetchone()
    conn.close()
    return jsonify(user_response(updated))


@app.route("/api/v1/surveys", methods=["POST"])
def create_survey():
    user, err = require_auth()
    if err:
        return err
    data = request.get_json(silent=True) or {}
    title = data.get("title", "").strip()
    link = data.get("link", "").strip()
    reward_points = int(data.get("reward_points", 0) or 0)
    if not title or not link:
        return error(422, "title and link required")
    if reward_points < 0:
        return error(422, "reward_points must be >= 0")

    if user["points"] < reward_points:
        return error(422, "not enough points to publish survey")

    survey_id = f"s_{uuid.uuid4().hex}"
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO surveys
            (id, owner_id, title, description, link, reward_points,
             deadline, estimated_minutes, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            survey_id,
            user["id"],
            title,
            data.get("description"),
            link,
            reward_points,
            data.get("deadline"),
            data.get("estimated_minutes"),
            "active",
            now_iso(),
        ),
    )
    if reward_points > 0:
        cur.execute(
            "UPDATE users SET points = points - ? WHERE id = ?",
            (reward_points, user["id"]),
        )
        cur.execute(
            """
            INSERT INTO points_logs (id, user_id, delta, reason, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                f"p_{uuid.uuid4().hex}",
                user["id"],
                -reward_points,
                "发布问卷消耗",
                now_iso(),
            ),
        )
    conn.commit()
    conn.close()
    return jsonify({"id": survey_id, "status": "active"})


@app.route("/api/v1/surveys", methods=["GET"])
def list_surveys():
    status = request.args.get("status")
    min_points = request.args.get("min_points")
    max_minutes = request.args.get("max_minutes")
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 20))
    offset = (page - 1) * page_size

    conditions = []
    params = []
    if status:
        conditions.append("status = ?")
        params.append(status)
    if min_points:
        conditions.append("reward_points >= ?")
        params.append(int(min_points))
    if max_minutes:
        conditions.append("estimated_minutes <= ?")
        params.append(int(max_minutes))

    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM surveys {where}", params)
    total = cur.fetchone()[0]
    cur.execute(
        f"""
        SELECT id, title, reward_points, estimated_minutes, deadline
        FROM surveys
        {where}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """,
        params + [page_size, offset],
    )
    items = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(
        {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
        }
    )


@app.route("/api/v1/surveys/<survey_id>", methods=["GET"])
def get_survey(survey_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,))
    survey = cur.fetchone()
    conn.close()
    if not survey:
        return error(404, "survey not found")
    return jsonify(dict(survey))


@app.route("/api/v1/surveys/<survey_id>/close", methods=["POST"])
def close_survey(survey_id):
    user, err = require_auth()
    if err:
        return err
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,))
    survey = cur.fetchone()
    if not survey:
        conn.close()
        return error(404, "survey not found")
    if survey["owner_id"] != user["id"]:
        conn.close()
        return error(403, "not survey owner")
    cur.execute(
        "UPDATE surveys SET status = ? WHERE id = ?",
        ("closed", survey_id),
    )
    conn.commit()
    conn.close()
    return jsonify({"id": survey_id, "status": "closed"})


@app.route("/api/v1/surveys/<survey_id>/fills", methods=["POST"])
def submit_fill(survey_id):
    user, err = require_auth()
    if err:
        return err
    data = request.get_json(silent=True) or {}
    duration = data.get("duration_seconds")
    evidence = data.get("evidence")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,))
    survey = cur.fetchone()
    if not survey:
        conn.close()
        return error(404, "survey not found")
    if survey["status"] != "active":
        conn.close()
        return error(422, "survey not active")
    if survey["owner_id"] == user["id"]:
        conn.close()
        return error(422, "cannot fill your own survey")

    cur.execute(
        "SELECT 1 FROM fills WHERE survey_id = ? AND user_id = ?",
        (survey_id, user["id"]),
    )
    if cur.fetchone():
        conn.close()
        return error(422, "already filled")

    fill_id = f"f_{uuid.uuid4().hex}"
    cur.execute(
        """
        INSERT INTO fills
            (id, survey_id, user_id, duration_seconds, status, points_awarded, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            fill_id,
            survey_id,
            user["id"],
            duration,
            "pending",
            0,
            now_iso(),
        ),
    )
    conn.commit()
    conn.close()
    return jsonify({"id": fill_id, "status": "pending", "points_awarded": 0, "evidence": evidence})


@app.route("/api/v1/fills/<fill_id>/review", methods=["POST"])
def review_fill(fill_id):
    user, err = require_auth()
    if err:
        return err
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if status not in ("approved", "rejected"):
        return error(422, "status must be approved or rejected")

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT fills.*, surveys.owner_id, surveys.reward_points
        FROM fills
        JOIN surveys ON fills.survey_id = surveys.id
        WHERE fills.id = ?
        """,
        (fill_id,),
    )
    record = cur.fetchone()
    if not record:
        conn.close()
        return error(404, "fill record not found")
    if record["owner_id"] != user["id"]:
        conn.close()
        return error(403, "not survey owner")
    if record["status"] != "pending":
        conn.close()
        return error(422, "record already reviewed")

    points_awarded = 0
    if status == "approved":
        points_awarded = record["reward_points"]
        cur.execute(
            "UPDATE users SET points = points + ?, activity_points = activity_points + ? WHERE id = ?",
            (points_awarded, points_awarded, record["user_id"]),
        )
        cur.execute(
            """
            INSERT INTO points_logs (id, user_id, delta, reason, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                f"p_{uuid.uuid4().hex}",
                record["user_id"],
                points_awarded,
                "完成问卷",
                now_iso(),
            ),
        )

    cur.execute(
        "UPDATE fills SET status = ?, points_awarded = ? WHERE id = ?",
        (status, points_awarded, fill_id),
    )
    conn.commit()
    conn.close()
    return jsonify({"id": fill_id, "status": status, "points_awarded": points_awarded})


@app.route("/api/v1/fills/me", methods=["GET"])
def list_my_fills():
    user, err = require_auth()
    if err:
        return err
    status = request.args.get("status")
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 20))
    offset = (page - 1) * page_size

    conditions = ["user_id = ?"]
    params = [user["id"]]
    if status:
        conditions.append("status = ?")
        params.append(status)
    where = "WHERE " + " AND ".join(conditions)

    conn = get_db()
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM fills {where}", params)
    total = cur.fetchone()[0]
    cur.execute(
        f"""
        SELECT id, survey_id, status, created_at
        FROM fills
        {where}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """,
        params + [page_size, offset],
    )
    items = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(
        {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
        }
    )


@app.route("/api/v1/points/logs", methods=["GET"])
def list_points_logs():
    user, err = require_auth()
    if err:
        return err
    log_type = request.args.get("type")
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 20))
    offset = (page - 1) * page_size

    conditions = ["user_id = ?"]
    params = [user["id"]]
    if log_type == "earn":
        conditions.append("delta > 0")
    elif log_type == "spend":
        conditions.append("delta < 0")
    where = "WHERE " + " AND ".join(conditions)

    conn = get_db()
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM points_logs {where}", params)
    total = cur.fetchone()[0]
    cur.execute(
        f"""
        SELECT id, delta, reason, created_at
        FROM points_logs
        {where}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """,
        params + [page_size, offset],
    )
    items = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(
        {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
        }
    )


@app.route("/api/v1/reports", methods=["POST"])
def create_report():
    user, err = require_auth()
    if err:
        return err
    data = request.get_json(silent=True) or {}
    target_type = data.get("target_type", "").strip()
    target_id = data.get("target_id", "").strip()
    reason = data.get("reason", "").strip()
    if not target_type or not target_id or not reason:
        return error(422, "target_type, target_id, reason required")

    report_id = f"r_{uuid.uuid4().hex}"
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO reports (id, reporter_id, target_type, target_id, reason, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            report_id,
            user["id"],
            target_type,
            target_id,
            reason,
            "pending",
            now_iso(),
        ),
    )
    conn.commit()
    conn.close()
    return jsonify({"id": report_id, "status": "pending"})


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
