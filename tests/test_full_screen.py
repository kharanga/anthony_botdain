from test_vault import PIN, SPECIMEN_LABEL, add_specimen_document, vault_with_specimen_document


def brightness_card(client):
    return client.get("/api/display/brightness").json()


def open_full_screen(client, document_id):
    return client.post(f"/api/vault/documents/{document_id}/full-screen")


def test_opening_a_document_full_screen_sets_maximum_brightness(client):
    document_id = vault_with_specimen_document(client)["documents"][0]["id"]
    before = brightness_card(client)

    response = open_full_screen(client, document_id)
    during = brightness_card(client)

    assert before["kind"] == "display"
    assert before["level"] < before["max_level"]
    assert response.status_code == 200
    assert during["level"] == during["max_level"]


def close_full_screen(client):
    return client.post("/api/vault/full-screen/close")


def test_closing_the_full_screen_view_restores_the_previous_brightness(client):
    document_id = vault_with_specimen_document(client)["documents"][0]["id"]
    level_before = brightness_card(client)["level"]
    open_full_screen(client, document_id)

    closed = close_full_screen(client).json()

    assert closed["level"] == level_before
    assert brightness_card(client)["level"] == level_before
    assert brightness_card(client)["full_screen_document_id"] is None


def test_full_screen_card_shows_only_the_one_document(client):
    vault_with_specimen_document(client)
    second_document_id = add_specimen_document(client).json()["documents"][0]["id"]

    card = open_full_screen(client, second_document_id).json()
    open_card = client.get("/api/vault/full-screen").json()

    assert card["title"] == SPECIMEN_LABEL
    assert [document["id"] for document in card["documents"]] == [second_document_id]
    assert open_card["photo_url"] == card["photo_url"]
    assert client.get(card["photo_url"]).status_code == 200


def test_opening_twice_still_restores_the_brightness_from_before_the_first_open(client):
    document_id = vault_with_specimen_document(client)["documents"][0]["id"]
    level_before = brightness_card(client)["level"]

    open_full_screen(client, document_id)
    open_full_screen(client, document_id)
    close_full_screen(client)

    assert brightness_card(client)["level"] == level_before


def test_locked_vault_opens_nothing_full_screen_and_leaves_brightness_alone(client):
    added_card = vault_with_specimen_document(client)
    document_id = added_card["documents"][0]["id"]
    client.post("/api/vault/lock")
    level_before = brightness_card(client)["level"]

    response = open_full_screen(client, document_id)

    assert response.status_code == 423
    assert SPECIMEN_LABEL not in response.text
    assert response.json()["detail"]["vault_state"] == "locked"
    assert brightness_card(client)["level"] == level_before


def test_locking_while_full_screen_hides_the_document_and_restores_brightness(client):
    added_card = vault_with_specimen_document(client)
    document_id = added_card["documents"][0]["id"]
    level_before = brightness_card(client)["level"]
    open_full_screen(client, document_id)

    client.post("/api/vault/lock")
    open_view = client.get("/api/vault/full-screen")

    assert open_view.status_code == 423
    assert SPECIMEN_LABEL not in open_view.text
    assert client.get(added_card["photo_url"]).status_code == 423
    assert brightness_card(client)["level"] == level_before
    assert brightness_card(client)["full_screen_document_id"] is None


def test_unknown_document_does_not_open_full_screen(client):
    client.post("/api/vault/pin", json={"pin": PIN})
    level_before = brightness_card(client)["level"]

    response = open_full_screen(client, 999)

    assert response.status_code == 404
    assert brightness_card(client)["level"] == level_before


def test_full_screen_page_has_nothing_but_the_document(client):
    response = client.get("/vault/full-screen/1")

    assert response.status_code == 200
    assert "/full-screen" in response.text
    assert "/api/vault/full-screen/close" in response.text
    assert 'id="full-screen-photo"' in response.text
    assert "<form" not in response.text
    assert 'href="/"' not in response.text


def test_vault_page_links_each_document_to_the_full_screen_view(client):
    assert "/vault/full-screen/" in client.get("/vault").text
