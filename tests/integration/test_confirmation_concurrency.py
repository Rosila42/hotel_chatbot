from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor


def test_concurrent_confirmation_single_execution(client, housekeeping_headers):
    request_response = client.post(
        "/chat",
        json={"message": "report dirty room 214"},
        headers=housekeeping_headers,
    )
    assert request_response.status_code == 200, request_response.text

    request_body = request_response.json()
    assert request_body["success"] is False
    assert request_body["command"] == "CREATE_INCIDENT"
    session_id = request_body["session_id"]

    def confirm():
        return client.post(
            "/chat",
            json={"message": "confirm", "session_id": session_id},
            headers=housekeeping_headers,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = [future.result() for future in (pool.submit(confirm), pool.submit(confirm))]

    assert all(response.status_code == 200 for response in results), [
        response.text for response in results
    ]

    bodies = [response.json() for response in results]
    successes = [body for body in bodies if body["success"] is True]
    consumed = [
        body
        for body in bodies
        if "already consumed" in body.get("message", "").lower()
    ]

    assert len(successes) == 1, bodies
    assert successes[0]["command"] == "CREATE_INCIDENT"
    assert len(consumed) == 1, bodies
    assert consumed[0]["success"] is False
