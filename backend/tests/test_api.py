"""
FastAPI Integration & Endpoint Verification Tests (Phase 7)
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "BioForge"


def test_api_molecules_endpoints(client):
    res = client.get("/api/molecules?limit=5")
    assert res.status_code == 200
    items = res.json()
    assert isinstance(items, list)
    if len(items) > 0:
        first_id = items[0]["id"]
        detail_res = client.get(f"/api/molecules/{first_id}")
        assert detail_res.status_code == 200
        detail = detail_res.json()
        assert "canonical_smiles" in detail
        assert "svg_2d" in detail


def test_api_predictions_endpoint(client):
    aspirin = "CC(=O)Oc1ccccc1C(=O)O"
    res = client.post("/api/predictions", json={"smiles": aspirin})
    assert res.status_code == 200
    data = res.json()
    assert data["smiles"] == aspirin
    assert "predicted_value" in data
    assert data["unit"] == "log mol/L"


def test_api_models_endpoint(client):
    res = client.get("/api/models")
    assert res.status_code == 200
    models = res.json()
    assert len(models) >= 2
    assert any("xgb" in m["id"] for m in models)


def test_api_experiments_endpoint(client):
    res = client.get("/api/experiments")
    assert res.status_code == 200
    exps = res.json()
    assert len(exps) >= 1

    comp_res = client.get("/api/experiments/comparison/latest")
    assert comp_res.status_code == 200
    comp = comp_res.json()
    assert "models" in comp
    assert "xgboost" in comp["models"]
    assert "gnn" in comp["models"]


def test_api_literature_search_endpoint(client):
    res = client.post("/api/literature/search", json={"query": "Delaney aqueous solubility", "top_k": 2})
    assert res.status_code == 200
    data = res.json()
    assert data["total_found"] > 0
    assert len(data["evidence"]) > 0


def test_api_rag_query_endpoint(client):
    res = client.post(
        "/api/rag/query",
        json={
            "question": "How does Delaney ESOL estimate aqueous solubility?",
            "smiles": "CCO",
            "top_k": 2,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data["citations"]) > 0
    assert data["confidence"] > 0
    assert data["molecular_context"] is not None


def test_api_jobs_endpoint(client):
    # Submit prediction job
    res = client.post("/api/jobs/prediction?smiles=CCO&model_type=xgboost")
    assert res.status_code == 200
    job = res.json()
    assert "job_id" in job
    job_id = job["job_id"]

    # Poll status
    status_res = client.get(f"/api/jobs/{job_id}")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["job_id"] == job_id
