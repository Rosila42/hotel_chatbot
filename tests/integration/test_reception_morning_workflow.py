def test_morning_reception_full_flow(client, reception_headers):
    # Step 1: arrivals
    r = client.post("/chat", json={"text": "today's arrivals"}, headers=reception_headers)
    assert r.json()["kind"] == "SUCCESS"

    # Step 2: room status
    r = client.post("/chat", json={"text": "which rooms aren't ready"}, headers=reception_headers)
    assert r.json()["kind"] == "SUCCESS"

    # Step 3: create incident
    r = client.post("/chat", json={"text": "report dirty room 214"}, headers=reception_headers)
    assert "CONFIRM" in r.json()["kind"] or r.json()["kind"] == "AWAITING_CONFIRMATION"

    # Step 4: confirm
    r = client.post("/chat", json={"text": "confirm"}, headers=reception_headers)
    assert r.json()["kind"] == "SUCCESS"

    # Step 5: operational summary
    r = client.post("/chat", json={"text": "operational summary"}, headers=reception_headers)
    assert r.json()["kind"] == "SUCCESS"