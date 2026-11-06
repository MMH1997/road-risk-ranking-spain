# Input data

Nothing in `data/raw/` is versioned. Put the files below there (or point `DGT_DATA_DIR` to another folder).

| File | What it is | Where from |
|---|---|---|
| `TABLA_ACCIDENTES_22.XLSX` … `TABLA_ACCIDENTES_25.XLSX` | Crash microdata: one row per road crash with at least one casualty (73 variables). | Spanish traffic authority (DGT), annual crash microdata. |
| `Diccionario_Tabla_Accidentes.xlsx` | Data dictionary used to decode the categorical variables. | DGT, with the microdata. |
| `67988.xlsx` | Resident population by province and year, 2022–2025. | INE, table 67988. |
| `puntosKilometricosSpain.csv` | Layer of kilometre markers (≈189 000 points on ≈13 800 roads, compiled in 2022). | Downloaded automatically by the notebook from `PK_URL` if it is missing. Check its licence, and replace it with the current IGN/CNIG layer for a publication. |
| `spain-provinces.geojson` | Simplified province polygons for the point-in-province check (Section 12.4). | Downloaded automatically from the URL in that cell. For a publication use the INE/CNIG boundaries. |

Optional: a table of the vehicle fleet by province (`FLEET_FILE`, Section 12.5), and a CSV of hospitals (`HOSPITALS_CSV`).

## Traceability

Each run of the notebook writes `outputs/manifest.json` with the date, the library versions, the key settings and the SHA-256 of every input file. Compare it with the one you cite to check that two runs used the same inputs.
