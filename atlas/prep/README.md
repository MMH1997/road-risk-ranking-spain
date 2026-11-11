# Regenerating the atlas data

`atlas/src/data.json` holds the aggregates the atlas shows (province estimates, cell counts, simplified map paths, nearby municipalities). It is built from three inputs:

1. **`dgt_tables.xlsx`**, written by the notebook (`outputs/`).
2. **Province boundaries** (INE/CNIG, any format `geopandas` reads) with a `COD_PROVINCIA` column holding the INE code.
3. **A municipality table** (pickle) with columns `name`, `pop`, `prov`, `x`, `y` (ETRS89 / UTM 30N, metres): municipal centroids and population on 1 January 2021. The one used here comes from the open SoftLine Spanish geographic database; any equivalent INE/CNIG-based table works. Its terms apply to what is embedded in the atlas.

```bash
python atlas/prep/prepare_atlas_data.py \
    --tables outputs/dgt_tables.xlsx \
    --provinces path/to/provincias_ine.gpkg \
    --municipalities path/to/muni.pkl \
    --out atlas/src/data.json
python atlas/build_atlas.py
```

Needs `geopandas`, `shapely`, `scipy`, `pandas` and `numpy`.

**Note on consistency.** The posterior summaries (rate ratios and ranks) in `data.json` come from one run of the Bayesian models. A new run changes them slightly because of Monte Carlo error (ranks by one or two places, rate ratios by a few hundredths). Rebuild the atlas from the same `dgt_tables.xlsx` that you use for the paper's tables, so that both agree.
