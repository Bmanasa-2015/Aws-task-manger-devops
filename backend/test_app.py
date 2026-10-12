
from backend import app as app_module


def setup_function():
    # Reset in-memory data before each test.
    app_module.tasks.clear()
    app_module.next_id = 1


def setup_client():
    return app_module.app.test_client()


def test_health_endpoint():
    client = setup_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "healthy"}


def test_get_empty_task_list():
    client = setup_client()

    response = client.get("/api/tasks")

    assert response.status_code == 200
    assert response.get_json() == []


def test_create_task():
    client = setup_client()

    response = client.post(
        "/api/tasks",
        json={"title": "Learn AWS"}
    )

    assert response.status_code == 201

    task = response.get_json()
    assert task["id"] == 1
    assert task["title"] == "Learn AWS"
    assert task["completed"] is False


def test_reject_empty_task_title():
    client = setup_client()

    response = client.post(
        "/api/tasks",
        json={"title": "   "}
    )

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_update_task():
    client = setup_client()

    create_response = client.post(
        "/api/tasks",
        json={"title": "Learn Docker"}
    )
    assert create_response.status_code == 201

    response = client.put(
        "/api/tasks/1",
        json={"completed": True}
    )

    assert response.status_code == 200
    assert response.get_json()["completed"] is True


def test_delete_task():
    client = setup_client()

    client.post(
        "/api/tasks",
        json={"title": "Learn GitHub Actions"}
    )

    response = client.delete("/api/tasks/1")

    assert response.status_code == 200

    list_response = client.get("/api/tasks")
    assert list_response.get_json() == []


def test_task_not_found():
    client = setup_client()

    response = client.delete("/api/tasks/999")

    assert response.status_code == 404
