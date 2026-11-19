from concurrent.futures import ThreadPoolExecutor

from test_vault import PIN, WRONG_PIN, vault_with_specimen_document
from test_vault_auto_lock import clocked_client

FREE_WRONG_ATTEMPTS = 5
FIRST_WAIT_SECONDS = 30


def unlock(client, pin):
    return client.post("/api/vault/unlock", json={"pin": pin})


def locked_vault_after_wrong_pins(client, wrong_attempts):
    vault_with_specimen_document(client)
    client.post("/api/vault/lock")
    return [unlock(client, WRONG_PIN).status_code for _ in range(wrong_attempts)]


def test_after_five_wrong_pins_even_the_right_pin_must_wait(config_path):
    client, clock = clocked_client(config_path)
    with client:
        wrong_statuses = locked_vault_after_wrong_pins(client, FREE_WRONG_ATTEMPTS)

        refused = unlock(client, PIN)
        state = client.get("/api/vault/state").json()

    assert wrong_statuses == [401] * FREE_WRONG_ATTEMPTS
    assert refused.status_code == 429
    assert refused.json()["detail"]["vault_state"] == "locked"
    assert refused.json()["detail"]["unlock_retry_in_seconds"] == FIRST_WAIT_SECONDS
    assert state["vault_state"] == "locked"


def test_the_right_pin_works_once_the_wait_is_over(config_path):
    client, clock = clocked_client(config_path)
    with client:
        locked_vault_after_wrong_pins(client, FREE_WRONG_ATTEMPTS)

        clock.advance(FIRST_WAIT_SECONDS)
        unlocked = unlock(client, PIN)

    assert unlocked.status_code == 200
    assert unlocked.json()["vault_state"] == "unlocked"


def test_each_further_wrong_pin_doubles_the_wait(config_path):
    client, clock = clocked_client(config_path)
    with client:
        locked_vault_after_wrong_pins(client, FREE_WRONG_ATTEMPTS)
        clock.advance(FIRST_WAIT_SECONDS)

        sixth_wrong = unlock(client, WRONG_PIN)
        clock.advance(FIRST_WAIT_SECONDS)
        still_waiting = unlock(client, PIN)

    assert sixth_wrong.status_code == 401
    assert sixth_wrong.json()["detail"]["unlock_retry_in_seconds"] == 2 * FIRST_WAIT_SECONDS
    assert still_waiting.status_code == 429
    assert still_waiting.json()["detail"]["unlock_retry_in_seconds"] == FIRST_WAIT_SECONDS


def test_a_right_pin_clears_the_wrong_pin_count(config_path):
    client, clock = clocked_client(config_path)
    with client:
        locked_vault_after_wrong_pins(client, FREE_WRONG_ATTEMPTS - 1)
        unlock(client, PIN)
        client.post("/api/vault/lock")

        statuses = [unlock(client, WRONG_PIN).status_code for _ in range(FREE_WRONG_ATTEMPTS - 1)]
        statuses.append(unlock(client, PIN).status_code)

    assert statuses == [401] * (FREE_WRONG_ATTEMPTS - 1) + [200]


def test_setting_the_pin_twice_at_once_sets_it_only_once(client):
    with ThreadPoolExecutor(max_workers=4) as pool:
        responses = list(pool.map(lambda pin: client.post("/api/vault/pin", json={"pin": pin}), ["111111", "222222"] * 2))

    assert sorted(response.status_code for response in responses) == [200, 409, 409, 409]
