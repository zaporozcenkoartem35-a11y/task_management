from datetime import datetime, timedelta, timezone
import uuid
from httpx import AsyncClient


async def test_user_registration_and_login(ac: AsyncClient):
    uid = uuid.uuid4().hex[:6]
    payload = {
        "username": f"user_{uid}",
        "password": "Password123"
    }
    reg_res = await ac.post("/api/v1/auth/register", json=payload)
    assert reg_res.status_code == 201

    login_res = await ac.post("/api/v1/auth/login", data={
        "username": payload["username"],
        "password": payload["password"]
    })
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()


async def test_create_and_get_task(ac: AsyncClient, auth_headers: dict):
    deadline = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    payload = {
        "title": "fix auth bug",
        "description": "need to fix token check",
        "priority": "High",
        "deadline": deadline
    }
    create_res = await ac.post("/api/v1/tasks", json=payload, headers=auth_headers)
    assert create_res.status_code == 201
    task_id = create_res.json()["id"]

    get_res = await ac.get(f"/api/v1/tasks/{task_id}", headers=auth_headers)
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "fix auth bug"


async def test_change_task_status_to_in_progress(ac: AsyncClient, auth_headers: dict):
    deadline = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    payload = {
        "title": "write docs",
        "priority": "Medium",
        "deadline": deadline
    }
    create_res = await ac.post("/api/v1/tasks", json=payload, headers=auth_headers)
    assert create_res.status_code == 201
    task_id = create_res.json()["id"]

    status_res = await ac.patch(
        f"/api/v1/tasks/{task_id}/status",
        json={"new_status": "In Progress"},
        headers=auth_headers
    )
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "In Progress"


async def test_cannot_delete_task_in_progress(ac: AsyncClient, auth_headers: dict):
    deadline = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    payload = {
        "title": "refactor api",
        "priority": "Low",
        "deadline": deadline
    }
    create_res = await ac.post("/api/v1/tasks", json=payload, headers=auth_headers)
    assert create_res.status_code == 201
    task_id = create_res.json()["id"]

    await ac.patch(
        f"/api/v1/tasks/{task_id}/status",
        json={"new_status": "In Progress"},
        headers=auth_headers
    )

    del_res = await ac.delete(f"/api/v1/tasks/{task_id}", headers=auth_headers)
    assert del_res.status_code == 400