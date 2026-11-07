# Village Asset Mapping



### GIS-Based Urban Service Distribution and Potential Service-Gap Analysis



A Python-based GIS application that analyses the spatial distribution of mapped facilities across Bengaluru Urban using OpenStreetMap data and a 500m × 500m grid system.


## 1. Project Overview



Village Asset Mapping is a spatial analysis project designed to organise geographical assets, identify the distribution of essential services and highlight grid cells that have no mapped essential facilities.



The project uses OpenStreetMap (OSM) data, SQLite, GeoPandas and spatial analysis techniques to process more than 1.22 million geographical components.



The current implementation focuses on Bengaluru Urban.



## 2. Project Objectives



\- Process large geographical datasets efficiently.

\- Generate a consistent 500m × 500m spatial grid.

\- Assign geographical components to their corresponding grid cells.

\- Classify mapped facilities using OSM tags.

\- Analyse the distribution of essential services.

\- Identify potential service-gap locations.

\- Export results in CSV and GeoJSON formats.



## 3. Technology Stack



| Technology | Purpose |

|---|---|

| Python | Application development |

| SQLite | Geographical data storage |

| GeoPandas | Geospatial data processing |

| Pandas | Tabular data analysis |

| NumPy | Numerical operations |

| Shapely | Geometric operations |

| PyProj | Coordinate reference transformations |

| OpenStreetMap | Geographical source data |



## 4. Study Area and Spatial Configuration



\- Study area: Bengaluru Urban

\- Projected area: 2,198.75 km²

\- Grid dimensions: 500m × 500m

\- Generated grid cells: 9,196

\- Analysis CRS: EPSG:32643 (UTM Zone 43N)

\- Export CRS: EPSG:4326 (WGS 84)



The grid is clipped to the study-area boundary.



## 5. Methodology



### Step 1: Boundary Validation



The Bengaluru Urban GeoJSON boundary is validated and projected into EPSG:32643.



### Step 2: Grid Generation



A deterministic fishnet grid is generated with 500m nominal cell dimensions. Grid cells are clipped to the study boundary.



### Step 3: OSM Component Assignment



Geographical components are processed in batches and assigned to grid cells using spatial joins.



### Step 4: Facility Classification



A rule-based classification system interprets OpenStreetMap tags and organises relevant records into service groups.



Uncertain records are retained for review instead of being automatically assigned to potentially incorrect categories.



### Step 5: Grid-Level Service Analysis



Facility counts are aggregated by grid cell and service group.



Cells without mapped essential facilities are flagged as potential service-gap cells.



### Step 6: Export



The final analysis is exported as CSV and GeoJSON for further analysis and GIS visualisation.



## 6. Current Dataset Statistics



| Metric | Result |

|---|---:|

| OSM components processed | 1,221,387 |

| Grid cells | 9,196 |

| Grid assignments | 1,221,387 |

| Classification records | 1,221,387 |

| Classified records | 31,863 |

| Cells with mapped services | 3,393 |

| Potential service-gap cells | 5,803 |



### Classified Service Distribution



| Service group | Records |

|---|---:|

| Transport | 8,892 |

| Healthcare | 3,961 |

| Education | 3,771 |

| Public amenities | 3,767 |

| Financial | 2,680 |

| Commercial | 7,677 |

| Public services | 296 |

| Recreation | 269 |

| Emergency | 168 |



## 7. Project Structure



```text

VillageAssetMapping/

│

├── App/

│   ├── GridGenerator.py

│   ├── AssetGridAssigner.py

│   ├── FacilityClassifier.py

│   ├── FacilityClassificationManager.py

│   ├── GridServiceAnalyzer.py

│   └── Other application modules

│

├── Test/

│   └── Automated test files

│

├── BengaluruUrbanBoundary.geojson

├── VillageAssets.db

├── RunGridAssignment.py

├── RunFacilityClassification.py

├── RunGridServiceAnalysis.py

├── VerifyGridAssignment.py

├── VerifyFinalIntegrity.py

├── BengaluruGridServiceAnalysis.csv

├── BengaluruGridServiceAnalysis.geojson

├── requirements.txt

└── README.md

```



## 8. Installation



### Prerequisites



\- Python 3.13 or compatible Python version

\- Git

\- OpenStreetMap dataset imported into the project SQLite database

\- Bengaluru Urban boundary GeoJSON



### Clone the repository



```bash

git clone YOUR\_REPOSITORY\_URL

cd VillageAssetMapping

```



### Create a virtual environment



```bash

python -m venv .venv

```



### Activate the environment



Windows PowerShell:



```powershell

.\\.venv\\Scripts\\Activate.ps1

```



### Install dependencies



```bash

pip install -r requirements.txt

```



## 9. Running the Analysis



The analysis pipeline consists of three main execution stages.



### Stage 1: Assign OSM components to grid cells



```powershell

python .\\RunGridAssignment.py

```



### Stage 2: Classify facilities



```powershell

python .\\RunFacilityClassification.py

```



### Stage 3: Generate grid-level service analysis



```powershell

python .\\RunGridServiceAnalysis.py

```



The execution scripts require the relevant boundary file and pre-populated SQLite database.



## 10. Testing



Run the automated test suite:



```powershell

python -m unittest discover -s Test -p "Test\*.py" -v

```



The project currently has 114 passing automated tests.



## 11. Output Files



### BengaluruGridServiceAnalysis.csv



Contains grid-level service counts, component totals, review counts and potential service-gap indicators.



### BengaluruGridServiceAnalysis.geojson



Contains the grid geometries and corresponding analysis attributes, suitable for GIS applications such as QGIS.



## 12. Important Limitations



\- OpenStreetMap completeness and tagging quality vary across locations.

\- OSM way components are represented by average vertex coordinates in the current dataset, not complete geometries.

\- A grid cell without a mapped facility does not necessarily mean residents lack access to that service.

\- Facility counts do not measure population demand, service capacity or operational status.

\- Road-network routing and travel-time accessibility have not yet been implemented.

\- Classification results may require manual review.



## 13. Future Scope



\- Interactive web-based GIS dashboard.

\- Population-density-based service-gap analysis.

\- Road-network accessibility and travel-time modelling.

\- Classification review interface.

\- Analysis of facilities beyond administrative boundaries.

\- Integration with additional authoritative datasets.



## 14. Data Attribution



Geographical data is sourced from OpenStreetMap contributors.



© OpenStreetMap contributors.



OpenStreetMap data is available under the Open Database License (ODbL). Appropriate attribution and applicable licence requirements should be maintained when redistributing the data or derived database.



## 15. Project Status



The current version implements the core GIS processing pipeline, including spatial grid generation, OSM component assignment, rule-based facility classification, grid-level service analysis and geospatial exports.



\*\*Project:\*\* Village Asset Mapping  

\*\*Study Area:\*\* Bengaluru Urban  

\*\*Analysis Type:\*\* GIS-Based Urban Service Distribution and Potential Service-Gap Analysis



