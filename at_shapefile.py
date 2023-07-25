## AT Shapefile
# Last update: 2023-07-20


"""About: Austrian shapefile creation and manipulation using GeoPandas library in Python or sf library in R."""


###############
# Initial Setup
###############

# Erase all declared global variables
globals().clear()


# Import packages
import os
from io import BytesIO
import re
from urllib.request import Request, urlopen
from zipfile import ZipFile

import geopandas as gpd
from matplotlib import pyplot
import numpy as np
import pandas as pd
import requests

# import xlrd


# Set working directory
os.chdir(path=os.path.join(os.path.expanduser('~'), 'Downloads'))


##############
# AT Shapefile
##############

## Postlexikon
# Postlexikon - Source: Post AG, https://www.post.at/g/c/postlexikon

# Get page source
page_source = (
    urlopen(
        url=Request(
            url='https://www.post.at/g/c/postlexikon',
            headers={'User-Agent': 'Mozilla'},
        ),
    )
    .read()
    .decode(encoding='utf8')
)
page_source = page_source.split(sep='\n')


# Get latest PLZ Verzeichnis .xls file
plz_verzeichnis = [s for s in page_source if 'title="PLZ Verzeichnis"' in s][0]
plz_verzeichnis = re.sub(
    pattern=r'^.*href="(.*\.xls)?.*$',
    repl=r'\1',
    string=plz_verzeichnis,
)


# Download and import
at_postalcodes = (
    pd.read_excel(
        io=urlopen(
            url=Request(url=plz_verzeichnis, headers={'User-Agent': 'Mozilla'}),
        ).read(),
        sheet_name='Plz_Anhang',
        header=0,
        index_col=None,
        skiprows=0,
        skipfooter=0,
        dtype=None,
        engine='xlrd',
    )
    # Rename columns
    .rename(columns={'PLZ': 'postal_code', 'Ort': 'city', 'Bundesland': 'state'})
    # Change dtypes
    .astype(dtype={'postal_code': 'str'})
    # Create 'country' column
    .assign(country='AT')
    # Filter rows
    .query('adressierbar == "Ja"')
    # Select columns
    .filter(items=['country', 'postal_code', 'state', 'city'])
    # Transform columns
    .assign(
        state=lambda row: np.where(
            row['state'] == 'W',
            'Vienna',
            (
                np.where(
                    row['state'] == 'N',
                    'Lower Austria',
                    (
                        np.where(
                            row['state'] == 'B',
                            'Burgenland',
                            (
                                np.where(
                                    row['state'] == 'O',
                                    'Upper Austria',
                                    (
                                        np.where(
                                            row['state'] == 'Sa',
                                            'Salzburg',
                                            (
                                                np.where(
                                                    row['state'] == 'T',
                                                    'Tyrol',
                                                    (
                                                        np.where(
                                                            row['state'] == 'V',
                                                            'Vorarlberg',
                                                            (
                                                                np.where(
                                                                    row['state']
                                                                    == 'St',
                                                                    'Styria',
                                                                    (
                                                                        np.where(
                                                                            row['state']
                                                                            == 'K',
                                                                            'Carinthia',
                                                                            None,
                                                                        )
                                                                    ),
                                                                )
                                                            ),
                                                        )
                                                    ),
                                                )
                                            ),
                                        )
                                    ),
                                )
                            ),
                        )
                    ),
                )
            ),
        ),
    )
    # Rearrange rows
    .sort_values(by=['country', 'postal_code'], ignore_index=True)
)


# Delete objects
del page_source, plz_verzeichnis


## Austria, Municipality List sort by Identifier
# Österreichisch, Gemeindeliste sortiert nach Gemeindekennziffer - Source: Statistik Austria, https://www.statistik.at/services/tools/services/regionales/regionale-gliederungen/

# Download and import
at_municipalities = (
    pd.read_csv(
        filepath_or_buffer='https://www.statistik.at/verzeichnis/reglisten/gemliste_knz_en.csv',
        sep=';',
        header=0,
        index_col=None,
        skiprows=2,
        skipfooter=1,
        dtype=None,
        engine='python',
        encoding='utf8',
    )
    # Rename columns
    .rename(
        columns={
            'Municipality Name': 'municipality',
            'Municipality Code': 'municipality_code',
            'Postal Code of the Municipal': 'postal_code',
        },
    )
    # Change dtypes
    .astype(dtype={'municipality_code': 'str', 'postal_code': 'str'})
    # Select columns
    .filter(items=['municipality_code', 'municipality', 'postal_code'])
    # Rearrange rows
    .sort_values(by=['municipality_code'], ignore_index=True)
)


## Austria, Political Districts
# Österreich, Politische Bezirke - Source: Statistik Austria, https://www.statistik.at/services/tools/services/regionales/regionale-gliederungen/

# Download and import
at_political_districts = (
    pd.read_csv(
        filepath_or_buffer='http://www.statistik.at/verzeichnis/reglisten/polbezirke_en.csv',
        sep=';',
        header=0,
        index_col=None,
        skiprows=2,
        skipfooter=1,
        dtype=None,
        engine='python',
        encoding='utf8',
    )
    # Rename columns
    .rename(
        columns={
            'Federal Province': 'state',
            'Political District': 'political_district',
            'Pol. District Code': 'political_district_code',
        },
    )
    # Change dtypes
    .astype(dtype={'political_district_code': 'str'})
    # Select columns
    .filter(items=['political_district_code', 'political_district', 'state'])
    # Rearrange rows
    .sort_values(by=['political_district_code'], ignore_index=True)
)


## Austria, Municipalities with Localities and Postal Codes
# Österreich, Gemeinden mit Ortschaften und Postleitzahlen - Source: Statistik Austria, https://www.statistik.at/services/tools/services/regionales/regionale-gliederungen/

# Download and import
at_localities = (
    pd.read_csv(
        filepath_or_buffer='http://www.statistik.at/verzeichnis/reglisten/ortsliste.csv',
        sep=';',
        header=0,
        index_col=None,
        skiprows=2,
        skipfooter=1,
        dtype=None,
        engine='python',
        encoding='utf8',
    )
    # Rename columns
    .rename(
        columns={
            'Gemeindekennziffer': 'gemeindekennziffer',
            'Gemeindename': 'municipality',
            'Ortschaftsname': 'city',
            'Postleitzahl': 'postal_code',
        },
    )
    # Change dtypes
    .astype(dtype={'gemeindekennziffer': 'str', 'postal_code': 'str'})
    # Create 'postal_code' column
    .assign(
        political_district_code=lambda row: row['gemeindekennziffer'].str.slice(
            start=0,
            stop=3,
        ),
    )
    # Separate collapsed 'postal_code' column into multiple rows
    .assign(
        postal_code=lambda row: row['postal_code'].str.split(pat=' ', expand=False),
    ).explode(column=['postal_code'])
    # Select columns
    .filter(items=['political_district_code', 'postal_code'])
    # Remove duplicate rows
    .drop_duplicates(subset=None, keep='first', ignore_index=True)
    # Left join 'at_political_districts'
    .merge(
        at_political_districts,
        how='left',
        on=['political_district_code'],
        indicator=False,
    )
    # Select columns
    .filter(
        items=['state', 'political_district_code', 'political_district', 'postal_code'],
    )
    # Rearrange rows
    .sort_values(by=['political_district_code', 'postal_code'], ignore_index=True)
)


# Test
(
    at_localities[at_localities.duplicated(subset=['postal_code'], keep=False) is True]
    .reset_index(level=None, drop=True)
    .sort_values(by=['postal_code'], ignore_index=True)
)


## Division of Austria into municipalities
# Gliederung Österreichs in Gemeinden - Source: Statistik Austria, https://data.statistik.gv.at/web/meta.jsp?dataset=OGDEXT_GEM_1

# Download
with ZipFile(
    file=BytesIO(
        initial_bytes=requests.get(
            url='https://data.statistik.gv.at/data/OGDEXT_GEM_1_STATISTIK_AUSTRIA_20230101.zip',
            timeout=5,
        ).content,
    ),
    mode='r',
) as zip_file:
    zip_file.extractall(path='OGDEXT_GEM_1_STATISTIK_AUSTRIA_20230101')


# Import
at_shapefile = (
    gpd.read_file(
        filename='OGDEXT_GEM_1_STATISTIK_AUSTRIA_20230101/STATISTIK_AUSTRIA_GEM_20230101.shp',
        layer='STATISTIK_AUSTRIA_GEM_20230101',
        encoding='utf8',
    )
    # Rename columns
    .rename(columns={'g_id': 'municipality_code', 'g_name': 'municipality'})
    # Change dtypes
    .astype(dtype={'municipality_code': 'str'})
    # Left join 'at_municipalities'
    .merge(
        at_municipalities.filter(items=['municipality_code', 'postal_code']),
        how='left',
        on=['municipality_code'],
        indicator=False,
    )
    # Left join 'at_postalcodes'
    .merge(at_postalcodes, how='left', on=['postal_code'], indicator=False)
    # Select columns
    .filter(
        items=[
            'country',
            'state',
            'municipality_code',
            'municipality',
            'city',
            'postal_code',
            'geometry',
        ],
    )
    # Rearrange rows
    .sort_values(by=['country', 'postal_code'], ignore_index=True)
)


# Delete objects
del at_municipalities, at_postalcodes


# Austria Shapefile - state level (first-level administrative divisions of Austria)
(
    at_shapefile.filter(items=['state', 'geometry'])
    .dissolve(by='state', as_index=False, sort=True, dropna=True)
    .plot()
)

pyplot.show()


# Austria Shapefile - municipality level (third-level administrative divisions of Austria)
(
    at_shapefile.filter(items=['state', 'municipality', 'geometry'])
    .dissolve(by='municipality', as_index=False, sort=True, dropna=True)
    .plot()
)

pyplot.show()


# Austria Shapefile - postal code level
(
    at_shapefile.filter(items=['postal_code', 'geometry'])
    .dissolve(by='postal_code', as_index=False, sort=True, dropna=True)
    .plot()
)

pyplot.show()
