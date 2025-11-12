
# AURA

Analyzing Uncertainty & Risk in Administration.

Our project seeks to predict which counties are most at risk during a government shutdown by analyzing multiple socioeconomic and demographic data sources.

## Authors

- [@Brian Ou](https://github.com/jindoridodi)
- [@Rachel Tran](https://github.com/b0mung51)
- [@Beaumont Yin](https://github.com/ra2y)


## Environment Variables

To run this project, you will need to add the following environment variables to your .env file

`API_KEY`

`PROJECT_ID`

`ENDPOINT`
## Run Locally


Prerequisites

- Python 3.11 (project tested with 3.11.9)
- A virtual environment is recommended

Install dependencies:

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Run the predictor

```bash
  python run_predictor.py
```
Run the heatmap visualizer

```bash
  python main.py
```


## Demo

https://youtu.be/RSoM2ouYx2I

## Acknowledgements

Datasets used:

- [U.S. Bureau of Labor Statistics: Quarterly Census of Employment and Wages](https://www.bls.gov/cew/downloadable-data-files.htm)
- [U.S. Bureau of Labor Statistics: Local Area Unemployment Statistics](https://www.bls.gov/lau/tables.htm#mcounty)
- [U.S. Census Bureau: American Community Survey](https://www.census.gov/data/developers/data-sets/acs-5year.html)
- [Economic Policy Institute: U.S. Cost of Living](https://www.kaggle.com/datasets/asaniczka/us-cost-of-living-dataset-3171-counties?resource=download)
- [Simple Maps: United States Counties Database](https://simplemaps.com/data/us-counties)