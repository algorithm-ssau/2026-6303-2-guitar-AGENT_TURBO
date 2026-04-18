# filepath: tests/test_params_echo.py
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.agent.params_echo import parse_query_simple, format_params_for_display

client = TestClient(app)

# --- ТЕСТЫ: parse_query_simple (10 различных запросов) ---

def test_parse_query_1_strat_up_to():
    p = parse_query_simple("Найди стратокастер до 500$")
    assert p["type"] == "stratocaster"
    assert p["price_max"] == 500
    assert p["price_min"] is None

def test_parse_query_2_les_paul_range():
    p = parse_query_simple("Gibson Les Paul 800-1500$")
    assert p["type"] == "les paul"
    assert p["brand"] == "gibson"
    assert p["price_min"] == 800
    assert p["price_max"] == 1500

def test_parse_query_3_tele_rub_thousands():
    p = parse_query_simple("теле до 80 тыс руб")
    assert p["type"] == "telecaster"
    assert p["price_max"] == 800  # 80 000 / 100

def test_parse_query_4_empty_unknown():
    p = parse_query_simple("что такое P90")
    assert p["type"] is None
    assert p["brand"] is None
    assert p["price_max"] is None

def test_parse_query_5_acoustic_tags():
    p = parse_query_simple("акустик taylor для кантри и блюз")
    assert p["type"] == "acoustic"
    assert p["brand"] == "taylor"
    assert "country" in p["tags"]
    assert "blues" in p["tags"]

def test_parse_query_6_from_to_tags():
    p = parse_query_simple("prs от 1000 до 2000 метал")
    assert p["brand"] == "prs"
    assert p["price_min"] == 1000
    assert p["price_max"] == 2000
    assert "metal" in p["tags"]

def test_parse_query_7_rub_raw():
    p = parse_query_simple("ibanez 50000 руб")
    assert p["brand"] == "ibanez"
    assert p["price_max"] == 500  # 50000 / 100

def test_parse_query_8_bass_funk():
    p = parse_query_simple("бас гитара yamaha фанк")
    assert p["type"] == "bass"
    assert p["brand"] == "yamaha"
    assert "funk" in p["tags"]

def test_parse_query_9_english_and_symbol():
    p = parse_query_simple("martin acoustic <=1000 jazz")
    assert p["brand"] == "martin"
    assert p["type"] == "acoustic"
    assert p["price_max"] == 1000
    assert "jazz" in p["tags"]

def test_parse_query_10_rub_000():
    p = parse_query_simple("epiphone 40 000 руб")
    assert p["brand"] == "epiphone"
    assert p["price_max"] == 400

# --- ТЕСТЫ: format_params_for_display ---

def test_format_params_full():
    params = {"type": "stratocaster", "price_min": 500, "price_max": 1000, "brand": "fender", "tags": ["blues"]}
    res = format_params_for_display(params)
    assert res == {"type": "Stratocaster", "budget": "$500–$1000", "brand": "Fender", "tags": ["blues"]}

def test_format_params_partial():
    params = {"type": "telecaster", "price_min": None, "price_max": 800, "brand": None, "tags":[]}
    res = format_params_for_display(params)
    assert res == {"type": "Telecaster", "budget": "≤ $800", "brand": None, "tags":[]}

def test_format_params_empty():
    params = {"type": None, "price_min": None, "price_max": None, "brand": None, "tags":[]}
    res = format_params_for_display(params)
    assert res == {"type": None, "budget": None, "brand": None, "tags":[]}

# --- ТЕСТ: POST /api/query/parse ---

def test_api_query_parse_endpoint():
    response = client.post("/api/query/parse", json={"query": "Найди стратокастер до 500$"})
    assert response.status_code == 200
    
    data = response.json()
    assert data["type"] == "Stratocaster"
    assert data["budget"] == "≤ $500"
    assert data["brand"] is None
    assert data["tags"] ==[]

def test_api_query_parse_endpoint_full():
    response = client.post(
        "/api/query/parse", 
        json={"query": "fender telecaster 800-1200$ для блюз"}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["type"] == "Telecaster"
    assert data["budget"] == "$800–$1200"
    assert data["brand"] == "Fender"
    assert data["tags"] == ["blues"]