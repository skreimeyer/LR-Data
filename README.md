Little Rock Property Research
===========================

This repository holds the scripts used to retrieve and analyze basic statistical information
concerning real estate within the limits of the city of Little Rock. Data is stored in an
SQlite database (chosen for ease of implementation). This repository is essentially a collection
of tools used in the analysis of property data for one location from a specific sources.
Thus, a reader hoping to use these tools for the purpose of mapping property valuation patterns
or detecting anomalies in a location other than Little Rock will not be able to use them
immediately. However. the code may be instructive toward solving similar problems in other
locations.

Public records may not have utility equal to proprietary and expensive realtor databases,
they are, at least in this case, capable of illuminating regional trends and edge cases
in real estate. That said, your mileage may vary.

Source Data
----------------------------

Land ownership data was retrieved from PAGIS.org (Pulaski County GIS service). Registered agents
and officers of public companies were discovered through scraping Arkansas Secretary of State
records.

LR.db was originally populated through the command-line and a script to recreate that
process is not included in this repository (this is an uncomplicated operation. Read
the DBF from PAGIS as a CSV and save to SQL).

Much thanks to the Pulaski County Clerk. Without these publicly maintained data sources,
this research would not be accessible to people like me.

Summary of Scripts
------------------------------
CompanySearch - Select property owner names likely to represent companies (based on REGEX)
and make an HTTP POST request to the Arkansas SOS website for corporate data. Save results.

DBFexporter - Convert .dbf to .csv

detect_outliers - Uses conventional statistical methods to determine anomalous valuations
in properties based on local (NN) and city-wide averages. Thresholds are defined at the
start of the script and can be tweaked to provide more discriminating results. Discoveries
are saved to the Outlier Report text file, and the underlying dictionary object is saved to
the output_dict file as a pickled binary.

gen_json - Creates a convenient JSON file from a text file of LandCodes provided in the PAGIS
metadata

geoextract - Calculates the centroid of polygons specified in the GeoJSON from PAGIS and saves
them to the SQLite database

hexplot - Creates .png images of hex bin plots broken down by zoning code, and further broken
down by specific metrics (appraised value, appraised value per acre and ratio of appraised
and assessed values). Colormapping makes large-scale trends very easy to visualize

hist_plotter - Creates .png images of histogram plots boken down by zoning code and further
broken down by specific metrics.

intloader - Recasts PAGIS data stored in SQLite into more appropriate numerical types (INT/FLOAT)

sanitizer - Owner names are not stored in a consistent format in the source data. This script
is an attempt to consolidate permutations of owner names which likely refer to the same person
or organization (ie 'ACME CO' = 'ACME COMPANY')
