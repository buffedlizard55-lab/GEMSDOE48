import sys, pathlib, json, hashlib, numpy as np, pytest
ROOT = pathlib.Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from gems48 import ds

def rand_bpa(rng, n=1000):
    f = rng.random(n) * 0.6; nn = rng.random(n) * (1 - f) * 0.9
    return f.astype(np.float32), nn.astype(np.float32), (1 - f - nn).astype(np.float32)

def test_dempster_normalised_and_commutative():
    rng = np.random.default_rng(0); m1, m2 = rand_bpa(rng), rand_bpa(rng)
    f, n, u, K = ds.dempster(m1, m2)
    assert np.allclose(f + n + u, 1, atol=1e-5) and (f >= 0).all() and (u >= 0).all()
    f2, n2, u2, K2 = ds.dempster(m2, m1)
    assert np.allclose(f, f2) and np.allclose(K, K2)

def test_yager_keeps_conflict_in_theta():
    rng = np.random.default_rng(1); m1, m2 = rand_bpa(rng), rand_bpa(rng)
    f, n, u, K = ds.yager(m1, m2)
    assert np.allclose(f + n + u, 1, atol=1e-5)
    assert (u >= K - 1e-6).all()

def test_vacuous_source_is_neutral():
    rng = np.random.default_rng(2); m1 = rand_bpa(rng)
    vac = (np.zeros(1000, np.float32), np.zeros(1000, np.float32), np.ones(1000, np.float32))
    f, n, u, K = ds.dempster(m1, vac)
    assert np.allclose(f, m1[0]) and np.allclose(K, 0)

def test_nms_min_spacing():
    rng = np.random.default_rng(3)
    score = rng.random((60, 60)); cand = rng.random((60, 60)) < 0.4
    sel = ds.nms_select(score, cand, 2.8)
    pts = np.argwhere(sel)
    d = np.hypot(*(pts[:, None, :] - pts[None, :, :]).transpose(2, 0, 1)); np.fill_diagonal(d, 99)
    assert d.min() >= 2.8 and (sel <= cand).all()

DL = ROOT / "docs/downloads"
@pytest.mark.skipif(not list(DL.glob("receipt-*.json")), reason="no shipped file")
def test_shipped_file_matches_receipt_and_is_valid():
    import rasterio
    rec = json.load(open(sorted(DL.glob("receipt-*.json"))[-1]))
    tif = DL / rec["file"]
    assert hashlib.sha256(tif.read_bytes()).hexdigest() == rec["sha256"]
    with rasterio.open(tif) as s:
        a = s.read(1); assert s.count == 1 and s.dtypes[0] == "float32" and s.crs.to_epsg() == 32611
        assert s.shape == (3730, 3292) and tuple(s.transform)[:6] == (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
    assert np.isfinite(a).all() and a.min() >= 0 and a.max() <= 1
    assert int((a > 0).sum()) == rec["emitted_px"] and rec["all_checks_passed"]

RAW = ROOT / "data/raw/scored"
@pytest.mark.skipif(not (RAW / "b2_02778.tif").exists(), reason="mirrors not fetched")
def test_every_dot_comes_from_a_live_scored_file():
    import rasterio
    rec = json.load(open(sorted(DL.glob("receipt-*.json"))[-1]))
    a = rasterio.open(DL / rec["file"]).read(1) > 0
    b2 = np.nan_to_num(rasterio.open(RAW / "b2_02778.tif").read(1)) > 0
    h32 = np.nan_to_num(rasterio.open(RAW / "h32tip_02649.tif").read(1)) > 0
    assert (a & ~(b2 | h32)).sum() == 0      # no invented positions
    assert (b2 & ~a).sum() == 0              # strict superset of the 0.2778 file
    assert int((a & ~b2).sum()) == 100
