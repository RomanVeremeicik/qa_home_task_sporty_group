"""
Config , use client fixture from conftest.py; TIMEOUT handled there.
These tests use full URLs to avoid base_url coupling.
tests/api/test_public_apis.py
"""
import time
import pytest


@pytest.mark.api
def test_dog_api_list_all_breeds(client):
    """Dog CEO: list all breeds, URL and status code 200"""
    url = "https://dog.ceo/api/breeds/list/all"
    r = client.get(url)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    j = r.json()
    assert j.get("status") == "success"
    assert isinstance(j.get("message"), dict)
    # At least one well-known breed present
    assert "hound" in j["message"] or "retriever" in j["message"] or len(j["message"]) > 0


@pytest.mark.api
@pytest.mark.parametrize("count", [1, 3])
def test_dog_api_random_image_message_is_url(client, count):
    """Dog CEO: get random image message from url"""
    url = f"https://dog.ceo/api/breeds/image/random/{count}"
    r = client.get(url)
    assert r.status_code == 200
    j = r.json()
    assert j.get("status") == "success"
    message = j.get("message")
    if isinstance(message, list):
        assert len(message) == count
        for u in message:
            assert isinstance(u, str) and (u.startswith("http://") or u.startswith("https://"))
    else:
        assert isinstance(message, str)
        assert message.startswith("http://") or message.startswith("https://")


@pytest.mark.api
@pytest.mark.parametrize("name", ["michael", "olga", "juan"])
def test_agify_returns_name_and_age(client, name):
    """Agify: prediction of age by name"""
    url = "https://api.agify.io"
    r = client.get(url, params={"name": name})
    assert r.status_code == 200
    j = r.json()
    assert j.get("name") == name
    assert "age" in j
    if j["age"] is not None:
        assert isinstance(j["age"], (int, float))
        assert j["age"] >= 0


@pytest.mark.api
def test_reqres_create_user_post(client):
    """
    POST https://reqres.in/api/users
    - retry on transient failures
    - if we consistently get 403 (remote policy/rate-limit), skip the test
    """
    url = "https://reqres.in/api/users"
    payload = {"name": "automation", "job": "qa"}

    headers = {
        "User-Agent": "qa-automation-tests/1.0",
        "Content-Type": "application/json"
    }

    max_attempts = 3
    backoff = 1.0
    last_status = None
    last_response = None

    for _ in range(1, max_attempts + 1):
        try:
            r = client.post(url, json=payload, headers=headers)
            last_status = r.status_code
            last_response = r
            # success codes historically 201 (created) — accept 200 too to be tolerant
            if r.status_code in (200, 201):
                j = r.json()
                assert j.get("name") == payload["name"]
                assert j.get("job") == payload["job"]
                assert "id" in j and isinstance(j["id"], str)
                assert "createdAt" in j
                return
            # If service responds with 403 (possible protection), retry a little then decide
            if r.status_code == 403:
                # small backoff then retry
                time.sleep(backoff)
                backoff *= 2
                continue
            # for other 5xx statuses, allow retry as well
            if 500 <= r.status_code < 600:
                time.sleep(backoff)
                backoff *= 2
                continue
            # otherwise break and fail
            break
        except ImportError:
            # network glitch — retry
            last_response = None
            last_status = None
            time.sleep(backoff)
            backoff *= 2
            continue

    # after attempts: decide result
    if last_status == 403:
        pytest.skip("ReqRes returned 403 Forbidden consistently —\
        external service policy/limiting (skipping test).")
    # If we have a last_response, raise informative assertion
    if last_response is not None:
        pytest.fail(f"Unexpected status {last_status}; response body: {last_response.text}")
    else:
        pytest.fail("Request to ReqRes failed repeatedly (no response).")


@pytest.mark.api
@pytest.mark.parametrize("pokemon", ["pikachu", "charizard", "bulbasaur"])
def test_pokemon_api_get_pokemon_has_name_and_types(client, pokemon):
    """Pokemon API: get pokemon by name and validate types"""
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon}"
    r = client.get(url)
    if r.status_code == 429:
        pytest.skip("Rate limited by PokeAPI (429)")
    assert r.status_code == 200
    j = r.json()
    assert j.get("name") == pokemon
    types = j.get("types")
    assert isinstance(types, list) and len(types) >= 1
    for t in types:
        assert "type" in t and "name" in t["type"]
