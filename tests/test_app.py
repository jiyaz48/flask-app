import pytest
from app import app, init_db


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path):
    """
    Isolates the database for every single test by using pytest's tmp_path.
    Creates a dedicated temporary SQLite database file and initializes the schema.
    """
    test_db = tmp_path / "test_tasks.db"
    app.config["TESTING"] = True
    app.config["DB_PATH"] = str(test_db)
    with app.app_context():
        init_db()
    yield


@pytest.fixture
def client():
    """
    Provides a Flask test client configured with the isolated test database.
    """
    with app.test_client() as test_client:
        yield test_client


# -------------------------------------------------------------------------
# Existing Compatibility Tests (Kept intact)
# -------------------------------------------------------------------------

def test_home_endpoint():
    """
    Preserves exact legacy test assertions for the home endpoint.
    """
    client = app.test_client()
    response = client.get("/")

    assert response.status_code == 200
    assert b"Welcome to My First DevOps Project!" in response.data


def test_health_endpoint():
    """
    Preserves exact legacy test assertions for the /health endpoint.
    """
    client = app.test_client()
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json["status"] == "healthy"
    assert response.json["message"] == "Application is running smoothly"


# -------------------------------------------------------------------------
# TaskFlow CRUD and Validation Tests
# -------------------------------------------------------------------------

def test_create_task_success(client):
    """
    Tests creating a new task with valid data.
    """
    response = client.post("/api/tasks", json={
        "title": "Set up CI/CD Pipeline",
        "description": "Configure GitHub Actions and SSM"
    })

    assert response.status_code == 201
    data = response.get_json()
    assert "task" in data
    assert data["task"]["title"] == "Set up CI/CD Pipeline"
    assert data["task"]["description"] == "Configure GitHub Actions and SSM"
    assert data["task"]["status"] == "pending"
    assert "id" in data["task"]


def test_create_task_validation(client):
    """
    Tests input validation on task creation (empty title, whitespace, missing body).
    """
    # Empty title
    res1 = client.post("/api/tasks", json={"title": ""})
    assert res1.status_code == 400
    assert "error" in res1.get_json()

    # Whitespace-only title
    res2 = client.post("/api/tasks", json={"title": "    "})
    assert res2.status_code == 400

    # Missing title field
    res3 = client.post("/api/tasks", json={"description": "no title"})
    assert res3.status_code == 400

    # Title exceeding 200 characters
    res4 = client.post("/api/tasks", json={"title": "A" * 201})
    assert res4.status_code == 400


def test_get_tasks_and_filtering(client):
    """
    Tests task listing and status filtering (?filter=all|pending|completed).
    """
    # Create two tasks
    client.post("/api/tasks", json={"title": "Task 1"})
    res2 = client.post("/api/tasks", json={"title": "Task 2"})
    task2_id = res2.get_json()["task"]["id"]

    # Toggle Task 2 to completed
    client.patch(f"/api/tasks/{task2_id}/toggle")

    # List all
    res_all = client.get("/api/tasks?filter=all")
    assert res_all.status_code == 200
    tasks_all = res_all.get_json()["tasks"]
    assert len(tasks_all) == 2

    # Filter pending
    res_pending = client.get("/api/tasks?filter=pending")
    assert res_pending.status_code == 200
    tasks_pending = res_pending.get_json()["tasks"]
    assert len(tasks_pending) == 1
    assert tasks_pending[0]["title"] == "Task 1"

    # Filter completed
    res_completed = client.get("/api/tasks?filter=completed")
    assert res_completed.status_code == 200
    tasks_completed = res_completed.get_json()["tasks"]
    assert len(tasks_completed) == 1
    assert tasks_completed[0]["title"] == "Task 2"


def test_update_task(client):
    """
    Tests updating a task's title and description.
    """
    create_res = client.post("/api/tasks", json={"title": "Initial Title", "description": "Initial Desc"})
    task_id = create_res.get_json()["task"]["id"]

    update_res = client.put(f"/api/tasks/{task_id}", json={
        "title": "Updated Title",
        "description": "Updated Desc"
    })
    assert update_res.status_code == 200
    updated_task = update_res.get_json()["task"]
    assert updated_task["title"] == "Updated Title"
    assert updated_task["description"] == "Updated Desc"

    # Test update with invalid title
    bad_res = client.put(f"/api/tasks/{task_id}", json={"title": ""})
    assert bad_res.status_code == 400


def test_toggle_task_status(client):
    """
    Tests toggling a task between pending and completed.
    """
    create_res = client.post("/api/tasks", json={"title": "Toggle Test"})
    task_id = create_res.get_json()["task"]["id"]

    # 1st toggle: pending -> completed
    toggle1 = client.patch(f"/api/tasks/{task_id}/toggle")
    assert toggle1.status_code == 200
    assert toggle1.get_json()["task"]["status"] == "completed"

    # 2nd toggle: completed -> pending
    toggle2 = client.patch(f"/api/tasks/{task_id}/toggle")
    assert toggle2.status_code == 200
    assert toggle2.get_json()["task"]["status"] == "pending"


def test_delete_task(client):
    """
    Tests deleting a task by ID.
    """
    create_res = client.post("/api/tasks", json={"title": "Delete Me"})
    task_id = create_res.get_json()["task"]["id"]

    delete_res = client.delete(f"/api/tasks/{task_id}")
    assert delete_res.status_code == 200

    # Ensure task no longer exists
    get_res = client.get("/api/tasks")
    task_ids = [t["id"] for t in get_res.get_json()["tasks"]]
    assert task_id not in task_ids

    # Deleting again returns 404
    delete_again = client.delete(f"/api/tasks/{task_id}")
    assert delete_again.status_code == 404


def test_task_not_found(client):
    """
    Tests 404 handling for non-existent task operations.
    """
    assert client.put("/api/tasks/9999", json={"title": "X"}).status_code == 404
    assert client.patch("/api/tasks/9999/toggle").status_code == 404
    assert client.delete("/api/tasks/9999").status_code == 404
