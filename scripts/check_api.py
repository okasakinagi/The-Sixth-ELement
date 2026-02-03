#!/usr/bin/env python3
import json
import os
import sys
import urllib.request
import urllib.error


def request_json(url, method="GET", data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {"error": raw}
        return exc.code, payload


def ensure_ok(status, payload, label):
    if 200 <= status < 300:
        print(f"[OK] {label}")
        return True
    print(f"[FAIL] {label}: HTTP {status} -> {payload}")
    return False


def main():
    base_url = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")
    email = os.environ.get("API_EMAIL", "zhangsan@example.com")
    password = os.environ.get("API_PASSWORD", "123456")

    print("== API Check ==")
    print(f"Base: {base_url}")
    print(f"User: {email}")

    status, payload = request_json(
        f"{base_url}/api/v1/auth/login",
        method="POST",
        data={"email": email, "password": password},
    )
    if not ensure_ok(status, payload, "Login"):
        return 1

    token = payload.get("access_token")
    if not token:
        print("[FAIL] Login: access_token missing")
        return 1

    ok = True
    status, payload = request_json(
        f"{base_url}/api/v1/task-hall/overview", token=token
    )
    ok &= ensure_ok(status, payload, "Task Hall Overview")

    status, payload = request_json(
        f"{base_url}/api/v1/task-hall/tasks?page=1&page_size=10", token=token
    )
    ok &= ensure_ok(status, payload, "Task Hall Tasks")

    status, payload = request_json(
        f"{base_url}/api/v1/surveys", token=token
    )
    ok &= ensure_ok(status, payload, "Survey Management List")

    # 默认用 2001，如果不存在可改环境变量
    survey_id = os.environ.get("API_SURVEY_ID", "2001")
    status, payload = request_json(
        f"{base_url}/api/v1/surveys/{survey_id}", token=token
    )
    ok &= ensure_ok(status, payload, f"Survey Detail ({survey_id})")

    if not ok:
        return 1

    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
