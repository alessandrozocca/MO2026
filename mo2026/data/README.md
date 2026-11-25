# Data: `debilt_coldest_day_per_winter.csv`

For each winter 1951-2026: the lowest daily mean temperature (°C) at De Bilt between 1 November and 31 March. The
winter labeled 1951 runs from November 1950 to March 1951. Columns: `winter`, `coldest_day_mean_C`,
`date_of_coldest_day`.

## Provenance

- **Source:** Royal Netherlands Meteorological Institute (KNMI), daily station data, station 260 (De Bilt), field TG
  (daily mean temperature, in 0.1 °C).
- **Retrieval:** 24 October 2026, from the KNMI daily-data service
  (`https://www.daggegevens.knmi.nl/klimatologie/daggegevens`, request `stns=260&vars=TG&start=19501101&end=20260331`).
- **Cross-check:** on 25 October 2026 all 27,545 daily TG values in the period matched the downloadable station file
  `etmgeg_260.zip`. [KNMI daily station downloads](https://www.knmi.nl/nederland-nu/klimatologie/daggegevens)
- **Extraction:** select station 260 and find the minimum TG in each November–March window. Where several days share
  the minimum, take the earliest date. Divide TG by 10 to obtain degrees Celsius.
- **Reproduction:** on 25 November 2026, the station download contained a TG value on each of the 27,545 days in
  the period. The extracted 76 winter minima reproduced the CSV byte for byte.

## Reuse

Source: KNMI (bron: KNMI). The course authors prepared this derived table and assignment independently of KNMI, with
no implied endorsement by KNMI. The repository's MIT license covers the code.

KNMI's copyright page describes CC0 for its website content unless otherwise stated. The daily-data download page
gives no separate license for the station files.
[KNMI website reuse terms](https://www.knmi.nl/copyright) · [KNMI daily station downloads](https://www.knmi.nl/nederland-nu/klimatologie/daggegevens)

## Homogenization

KNMI's daily-data page (consulted 25 October 2026) states that the temperature series of five principal stations,
including De Bilt, are homogenized. The data files themselves still carry KNMI's general warning that station series
may be inhomogeneous because of relocations and changes in instruments. KNMI also publishes separate homogenization
datasets.

The assignments use these winters as a realistic scenario set. They make no claim about climate trends: a comparison
of 45 earlier with 31 later winters is not a climate-attribution study.
