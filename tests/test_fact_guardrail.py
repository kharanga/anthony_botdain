RATE_QUESTION = {"question": "What is the rate?"}


def evidence_texts(card):
    return [item["text"] for item in card["evidence"]]


def test_a_reply_that_keeps_the_facts_passes_through(client, fake_model):
    fake_model.reply_with("Right now one US dollar buys ₡510, so 510 CRC per USD.")

    response = client.post("/api/ask/rate", json=RATE_QUESTION)

    assert response.status_code == 200
    card = response.json()
    assert card["kind"] == "answer"
    assert card["body"] == "Right now one US dollar buys ₡510, so 510 CRC per USD."
    assert "rate = 510 CRC per USD" in evidence_texts(card)


RATE_TEMPLATE_ANSWER = "The Rate is ₡510 per US dollar."


def asked_rate_card(client):
    response = client.post("/api/ask/rate", json=RATE_QUESTION)
    assert response.status_code == 200
    return response.json()


def test_a_reply_that_changes_the_number_falls_back_to_the_template(client, fake_model):
    fake_model.reply_with("One US dollar buys ₡520.")

    card = asked_rate_card(client)

    assert card["body"] == RATE_TEMPLATE_ANSWER
    assert "rate = 510 CRC per USD" in evidence_texts(card)


def test_a_reply_that_adds_a_number_falls_back_to_the_template(client, fake_model):
    fake_model.reply_with("One US dollar buys ₡510, and a casado costs about ₡3,500.")

    card = asked_rate_card(client)

    assert card["body"] == RATE_TEMPLATE_ANSWER
    assert "rate = 510 CRC per USD" in evidence_texts(card)


def test_a_reply_that_changes_the_currency_term_falls_back_to_the_template(client, fake_model):
    fake_model.reply_with("You get 510 euros for each pound.")

    card = asked_rate_card(client)

    assert card["body"] == RATE_TEMPLATE_ANSWER
    assert "rate = 510 CRC per USD" in evidence_texts(card)


def test_a_reply_that_adds_a_name_falls_back_to_the_template(client, fake_model):
    fake_model.reply_with("At Banco Nacional one US dollar buys ₡510.")

    card = asked_rate_card(client)

    assert card["body"] == RATE_TEMPLATE_ANSWER
    assert "rate = 510 CRC per USD" in evidence_texts(card)


def test_symbols_written_against_the_number_count_as_keeping_the_term(client, fake_model):
    fake_model.reply_with("You get ₡510 for every $1.")

    card = asked_rate_card(client)

    assert card["body"] == "You get ₡510 for every $1."


def test_a_reply_that_writes_the_same_number_differently_passes_through(client, fake_model):
    client.put("/api/rate", json={"colones_per_dollar": 505.5})
    fake_model.reply_with("Each US dollar is worth 505.50 colones.")

    card = asked_rate_card(client)

    assert card["body"] == "Each US dollar is worth 505.50 colones."
    assert "rate = 505.5 CRC per USD" in evidence_texts(card)


def test_the_template_answer_uses_the_current_rate(client, fake_model):
    client.put("/api/rate", json={"colones_per_dollar": 498})
    fake_model.reply_with("One US dollar buys ₡510.")

    card = asked_rate_card(client)

    assert card["body"] == "The Rate is ₡498 per US dollar."
    assert "rate = 498 CRC per USD" in evidence_texts(card)


def test_the_model_is_given_the_facts_to_phrase(client, fake_model):
    fake_model.reply_with("One US dollar buys ₡510.")

    asked_rate_card(client)

    sent_text = "".join(message["content"] for message in fake_model.last_request["messages"])
    assert "rate = 510 CRC per USD" in sent_text
    assert "What is the rate?" in sent_text


def test_the_template_answer_is_given_when_the_model_is_unavailable(client, fake_model):
    fake_model.fail_with(503)

    card = asked_rate_card(client)

    assert card["body"] == RATE_TEMPLATE_ANSWER
    assert "rate = 510 CRC per USD" in evidence_texts(card)


def test_a_reply_that_inverts_the_rate_falls_back_to_the_template(client, fake_model):
    fake_model.reply_with("One colón is worth 510 US dollars.")

    card = asked_rate_card(client)

    assert card["body"] == RATE_TEMPLATE_ANSWER


def test_a_reply_that_puts_the_dollar_sign_on_the_rate_falls_back_to_the_template(client, fake_model):
    fake_model.reply_with("You pay $510 for every ₡1.")

    card = asked_rate_card(client)

    assert card["body"] == RATE_TEMPLATE_ANSWER


def test_a_null_reply_content_falls_back_to_the_template(client, fake_model):
    fake_model.reply_with_message_content(None)

    card = asked_rate_card(client)

    assert card["body"] == RATE_TEMPLATE_ANSWER
