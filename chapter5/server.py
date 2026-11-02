"""画面（web/）のための API サーバ。

使い方: uv run --group mask python chapter5/server.py
"""

import threading
import time

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import secretary
from tools import load, mark_as_read, reset_workspace

app = FastAPI()
# 秘書の実行の状態。実行は1つずつ行う
status = {"running": False, "email_ids": [], "last_run": None}


class SecretaryRequest(BaseModel):
    email_ids: list[str]
    guard: bool = False


@app.get("/api/info")
def info():
    """この章の画面で使える機能を返す。"""
    return {"chapter": 5, "features": ["sent", "guard"]}


@app.get("/api/emails")
def list_emails():
    archived, read = load("archived.json"), load("read.json")
    drafts = {d["email_id"] for d in load("drafts.json")}
    history = load("history.json")
    emails = sorted(load("emails.json"), key=lambda e: e["date"], reverse=True)
    return [
        {
            "id": e["id"], "from": e["from"], "subject": e["subject"],
            "date": e["date"], "read": e["id"] in read,
            "archived": e["id"] in archived, "draft": e["id"] in drafts,
            "processed": e["id"] in history,
        }
        for e in emails
    ]


@app.get("/api/emails/{email_id}")
def get_email(email_id: str):
    for email in load("emails.json"):
        if email["id"] == email_id:
            drafts = [d["body"] for d in load("drafts.json")
                      if d["email_id"] == email_id]
            history = load("history.json").get(email_id)
            return {**email, "drafts": drafts, "history": history}
    raise HTTPException(404)


@app.post("/api/emails/{email_id}/read")
def read(email_id: str):
    mark_as_read(email_id)


@app.get("/api/tasks")
def tasks():
    return load("tasks.json")


@app.get("/api/events")
def events():
    return sorted(load("calendar.json"), key=lambda e: e["start"])


@app.post("/api/secretary", status_code=202)
def start_secretary(request: SecretaryRequest):
    """秘書の処理を始める。処理は裏で進み、状態は /api/status で確かめる。"""
    if status["running"]:
        raise HTTPException(409, "秘書が処理中です")
    status["running"] = True
    status["email_ids"] = request.email_ids

    def work():
        start = time.perf_counter()
        try:
            result = secretary.run(request.email_ids, request.guard)
            usage = result.metrics.accumulated_usage
            status["last_run"] = {
                "report": str(result),
                "seconds": round(time.perf_counter() - start),
                "input_tokens": usage["inputTokens"],
                "output_tokens": usage["outputTokens"],
            }
        except Exception as e:
            status["last_run"] = {"error": str(e)}
        finally:
            status["running"] = False

    threading.Thread(target=work, daemon=True).start()


@app.get("/api/status")
def get_status():
    return status


@app.post("/api/reset")
def reset():
    """データを初期状態に戻す。"""
    if status["running"]:
        raise HTTPException(409, "秘書が処理中です")
    reset_workspace()
    status["last_run"] = None


if __name__ == "__main__":
    # 起動するたびに、データを初期状態に戻す
    reset_workspace()
    uvicorn.run(app, host="127.0.0.1", port=8000)
