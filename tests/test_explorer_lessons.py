"""The teaching chart must use exact historical data, with explicit frames."""
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from suryasiddhanta.api.main import app
from suryasiddhanta.api.explorer_core import snapshot


def test_mars_lesson_series_is_bounded_sourced_and_exact():
    with TestClient(app) as client:
        response = client.get('/explorer/lessons/mars-retrograde')
    assert response.status_code == 200
    data = response.json()
    assert data['model'] == 'historical'
    assert data['body'] == 'Mars'
    assert data['origin'] == 'Earth'
    assert data['longitude_units'] == 'degrees'
    assert data['motion_units'] == 'degrees/day'
    assert data['frame'] and data['time_scale'] and data['provenance']
    samples = data['samples']
    assert 180 <= len(samples) <= 190
    assert samples[0]['instant'].startswith('2024-10-01')
    assert samples[-1]['instant'].startswith('2025-04-01')
    assert all(a['timestamp'] < b['timestamp'] for a, b in zip(samples, samples[1:]))
    january = next(s for s in samples if s['instant'].startswith('2025-01-01'))
    exact = snapshot('historical', datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp())
    assert january['longitude_deg'] == exact['bodies']['Mars']['longitude_deg']
    assert january['motion_deg_per_day'] == exact['bodies']['Mars']['motion_deg_per_day']
    assert january['motion_deg_per_day'] < 0
    assert samples[-1]['motion_deg_per_day'] > 0
