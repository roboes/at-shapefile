## AT Shapefile
# Last update: 2023-05-23


### About: Austrian shapefile creation and manipulation using GeoPandas library in Python or sf library in R.


###############
# Initial Setup
###############

# Import packages
packages_install <- function(packages){
	new.packages <- packages[!(packages %in% installed.packages()[, "Package"])]
	if (length(new.packages))
	install.packages(new.packages, dependencies = TRUE)
	sapply(packages, require, character.only = TRUE)
}

packages_required <- c("readxl", "sf", "tidyverse")
packages_install(packages_required)


# Set working directory
setwd("C:/Users/roboes/Downloads")


# Erase all declared global variables
rm(list=ls())




##############
# AT Shapefile
##############

## Postlexikon
# Postlexikon - Source: Post AG, https://www.post.at/g/c/postlexikon

# Download
download.file("https://assets.post.at/-/media/Dokumente/De/Geschaeftlich/Werben/PLZ_Verzeichnis-20230503.xls", "AT Postal Codes.xls", mode = "wb")


# Import
at_postalcodes <- read_excel(path = "AT Postal Codes.xls", sheet = "Plz_Anhang", col_names = TRUE) |>
	rename(postal_code = PLZ, city = Ort, state = Bundesland) |>
	mutate(across(c(postal_code), as.character)) |>
	mutate(country = "AT") |>
	filter(adressierbar == "Ja") |>
	select(country, postal_code, state, city) |>
	mutate(
		state = case_when(
			state == "W" ~ "Vienna",
			state == "N" ~ "Lower Austria",
			state == "B" ~ "Burgenland",
			state == "O" ~ "Upper Austria",
			state == "Sa" ~ "Salzburg",
			state == "T" ~ "Tyrol",
			state == "V" ~ "Vorarlberg",
			state == "St" ~ "Styria",
			state == "K" ~ "Carinthia",
		),
	) |>
	arrange(postal_code)



## Austria, Municipality List sort by Identifier
# Österreichisch, Gemeindeliste sortiert nach Gemeindekennziffer - Source: Statistik Austria, https://www.statistik.at/services/tools/services/regionales/regionale-gliederungen/


# Download and import
at_municipalities <- read_delim(file = "https://www.statistik.at/verzeichnis/reglisten/gemliste_knz_en.csv", delim = ";", skip = 2) |>
	slice(1:(n() - 1)) |>
	rename(municipality = "Municipality Name", municipality_code = "Municipality Code", postal_code = "Postal Code of the Municipal") |>
	mutate(across(c(municipality_code, postal_code), as.character)) |>
	select(municipality_code, municipality, postal_code) |>
	arrange(municipality_code)



## Austria, Political Districts
# Österreich, Politische Bezirke - Source: Statistik Austria, https://www.statistik.at/services/tools/services/regionales/regionale-gliederungen/

# Download and import
at_political_districts <- read_delim(file = "http://www.statistik.at/verzeichnis/reglisten/polbezirke_en.csv", delim = ";", skip = 2) |>
	slice(1:(n() - 1)) |>
	rename(state = "Federal Province", political_district = "Political District", political_district_code = "Pol. District Code") |>
	mutate(across(c("political_district_code"), as.character)) |>
	select(political_district_code, political_district, state) |>
	arrange(political_district_code)



## Austria, Municipalities with Localities and Postal Codes
# Österreich, Gemeinden mit Ortschaften und Postleitzahlen - Source: Statistik Austria, https://www.statistik.at/services/tools/services/regionales/regionale-gliederungen/

# Download and import
at_localities <- read_delim(file = "http://www.statistik.at/verzeichnis/reglisten/ortsliste.csv", delim = ";", skip = 2) |>
	slice(1:(n() - 1)) |>
	rename(
	gemeindekennziffer = "Gemeindekennziffer", municipality = "Gemeindename", city = "Ortschaftsname", postal_code = "Postleitzahl") |>
	mutate(across(c(gemeindekennziffer, postal_code), as.character)) |>
	mutate(
		political_district_code = substr(gemeindekennziffer, 1, 3)
	) |>
	separate_rows(postal_code, sep = " ") |>
	select(political_district_code, postal_code) |>
	distinct(political_district_code, postal_code) |>
	left_join(at_political_districts, by = c("political_district_code")) |>
	select(state, political_district_code, political_district, postal_code) |>
	arrange(political_district_code, postal_code)


# Test
at_localities |> group_by(postal_code) |> filter(n() >= 2) |> ungroup() |> arrange(postal_code)



## Division of Austria into municipalities
# Gliederung Österreichs in Gemeinden - Source: Statistik Austria, https://data.statistik.gv.at/web/meta.jsp?dataset=OGDEXT_GEM_1

# Download
download.file("https://data.statistik.gv.at/data/OGDEXT_GEM_1_STATISTIK_AUSTRIA_20230101.zip", "OGDEXT_GEM_1_STATISTIK_AUSTRIA_20230101.zip", mode = "wb")
unzip(zip = "OGDEXT_GEM_1_STATISTIK_AUSTRIA_20230101.zip", exdir = "OGDEXT_GEM_1_STATISTIK_AUSTRIA_20230101")

# Import
at_shapefile <- st_read(dsn = "OGDEXT_GEM_1_STATISTIK_AUSTRIA_20230101", layer = "STATISTIK_AUSTRIA_GEM_20230101") |>
	rename(municipality_code = "g_id", municipality = "g_name") |>
	mutate(across(c(municipality_code), as.character)) |>
	left_join(at_municipalities |> select(municipality_code, postal_code), by = c("municipality_code")) |>
	left_join(at_postalcodes, by = c("postal_code")) |>
	select(country, state, municipality_code, municipality, city, postal_code, geometry)


# Delete objects
rm(at_municipalities, at_postalcodes)



# Austria Shapefile - state level (first-level administrative divisions of Austria)
plot(at_shapefile |>
	select(state, geometry) |>
	group_by(state) |>
	summarise(geometry = st_union(geometry)) |>
	ungroup()
)


# Austria Shapefile - municipality level (third-level administrative divisions of Austria)
plot(at_shapefile |>
	select(state, municipality, geometry) |>
	group_by(state, municipality) |>
	summarise(geometry = st_union(geometry)) |>
	ungroup() |>
	select(municipality, geometry)
)


# Austria Shapefile - postal code level
plot(at_shapefile |>
	select(postal_code, geometry) |>
	group_by(postal_code) |>
	summarise(geometry = st_union(geometry)) |>
	ungroup()
)
