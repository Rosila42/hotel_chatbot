from sqlalchemy import inspect

from storage import engine


def test_application_startup_bootstraps_schema(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"] == "0.1.1"

    tables = set(inspect(engine).get_table_names())
    assert {
        "chat_sessions",
        "chat_messages",
        "automation_definitions",
        "automation_executions",
        "audit_records",
        "alembic_version",
    }.issubset(tables)
