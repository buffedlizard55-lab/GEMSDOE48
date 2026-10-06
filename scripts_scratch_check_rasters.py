import rasterio, numpy as np, json
files = {
 'dotted_h33_2_b2': 'data/raw/dotted_h33_2_b2_zeros.tif',
 'tip_h33d_stepover': 'data/raw/tip_h33d_stepover.tif',
 'tip_h32_1_prethin': 'data/raw/tip_h32_1_prethin_tip_euler.tif',
 'ref_h27_4_solo': 'data/raw/ref_h27_4_solo.tif',
 'ref_h36_1_rung30': 'data/raw/ref_h36_1_rung30.tif',
}
TEMPLATE_T = (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
for k, f in files.items():
    with rasterio.open(f) as ds:
        a = ds.read(1)
        ok_t = tuple(ds.transform) == TEMPLATE_T
        pos = a > 0
        fin = np.isfinite(a)
        print(f"{k:22s} shape={a.shape} crs={ds.crs.to_string() if ds.crs else None} "
              f"t_match={ok_t} dtype={a.dtype} nodata={ds.nodata} "
              f"n_pos={int(pos.sum())} min={np.nanmin(a):.4g} max={np.nanmax(a):.4g} "
              f"finite={int(fin.sum())} vals_pos={np.unique(a[pos])[:8]}")
