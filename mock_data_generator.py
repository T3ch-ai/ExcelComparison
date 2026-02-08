"""
Generates realistic mock data for both QES (Excel) and NIQ (Excel) datasets.
Phase 2: Full column structures with SSA/FIPS codes, coverage percentages,
detailed provider data including lat/long, taxonomy, facility vs individual.
Introduces controlled mismatches so the comparator has meaningful output.
"""

import random
import os
import pandas as pd
import numpy as np

# ============================================================================
# DATA SOURCES (publicly available reference data)
# ============================================================================
# All reference data in this file is derived from the following public sources:
#
# 1. SSA-FIPS County Code Crosswalk
#    Source: NBER (compiled from CMS Medicare Advantage Ratebook data)
#    URL:    https://www.nber.org/research/data/ssa-federal-information-processing-series-fips-state-and-county-crosswalk
#    File:   ssa_fips_state_county_2024.csv
#    Note:   SSA state codes differ from FIPS state codes (TX: SSA=45, FIPS=48;
#            WI: SSA=52, FIPS=55). County codes also differ between systems.
#
# 2. FIPS County Codes
#    Source: US Census Bureau
#    URL:    https://www.census.gov/library/reference/code-lists/ansi.html
#    Note:   5-digit codes: 2-digit state + 3-digit county
#
# 3. County Classifications (Metro/Micro/Rural/CEAC)
#    Source: OMB Core Based Statistical Area (CBSA) Delineations
#    URL:    https://www.census.gov/geographies/reference-files/time-series/demo/metro-micro/delineation-files.html
#    Note:   Metro = Metropolitan Statistical Area (urban core >= 50,000)
#            Micro = Micropolitan Statistical Area (urban core 10,000-49,999)
#            Rural = not in any CBSA
#            CEAC  = CMS Counties with Extreme Access Considerations
#
# 4. NUCC Health Care Provider Taxonomy Codes
#    Source: National Uniform Claim Committee (NUCC)
#    URL:    https://taxonomy.nucc.org/
#    Note:   10-character alphanumeric codes identifying provider specialties
#
# 5. CMS Provider Specialty Types
#    Source: CMS Medicare Provider/Supplier Type codes
#    URL:    https://www.cms.gov/medicare/enrollment-renewal/providers-suppliers/chain-ownership-system/specialty-codes-provider-type
#
# 6. NPI (National Provider Identifier)
#    Source: 45 CFR 162.410 -- 10-digit numeric identifier
#    URL:    https://nppes.cms.hhs.gov/
#
# 7. EIN / TIN (Employer Identification Number / Tax ID)
#    Source: IRS -- 9-digit numeric identifier (format: XX-XXXXXXX)
#    URL:    https://www.irs.gov/businesses/small-businesses-self-employed/employer-id-numbers
#
# 8. Geographic Coordinates
#    Source: US Census Bureau TIGER/Line Shapefiles (county centroids)
#    URL:    https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html
#
# 9. ZIP Code Ranges by State
#    Source: USPS Publication 65 -- National Five-Digit ZIP Code & Post Office Directory
#    URL:    https://postalpro.usps.com/
# ============================================================================

# ============================================================================
# Reference Data
# ============================================================================

STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii",
    "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine",
    "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska",
    "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico",
    "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island",
    "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas",
    "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}

# SSA state codes (from NBER SSA-FIPS crosswalk, includes AS=03 and VI=49 in sequence)
# Source: https://www.nber.org/research/data/ssa-federal-information-processing-series-fips-state-and-county-crosswalk
SSA_STATE_CODES = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06",
    "CO": "07", "CT": "08", "DE": "09", "DC": "10", "FL": "11",
    "GA": "12", "HI": "13", "ID": "14", "IL": "15", "IN": "16",
    "IA": "17", "KS": "18", "KY": "19", "LA": "20", "ME": "21",
    "MD": "22", "MA": "23", "MI": "24", "MN": "25", "MS": "26",
    "MO": "27", "MT": "28", "NE": "29", "NV": "30", "NH": "31",
    "NJ": "32", "NM": "33", "NY": "34", "NC": "35", "ND": "36",
    "OH": "37", "OK": "38", "OR": "39", "PA": "40", "RI": "41",
    "SC": "42", "SD": "43", "TN": "44", "TX": "45", "UT": "46",
    "VT": "47", "VA": "48", "WA": "50", "WV": "51", "WI": "52",
    "WY": "53",
}

# FIPS state codes (US Census Bureau standard)
FIPS_STATE_CODES = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06",
    "CO": "08", "CT": "09", "DE": "10", "DC": "11", "FL": "12",
    "GA": "13", "HI": "15", "ID": "16", "IL": "17", "IN": "18",
    "IA": "19", "KS": "20", "KY": "21", "LA": "22", "ME": "23",
    "MD": "24", "MA": "25", "MI": "26", "MN": "27", "MS": "28",
    "MO": "29", "MT": "30", "NE": "31", "NV": "32", "NH": "33",
    "NJ": "34", "NM": "35", "NY": "36", "NC": "37", "ND": "38",
    "OH": "39", "OK": "40", "OR": "41", "PA": "42", "RI": "44",
    "SC": "45", "SD": "46", "TN": "47", "TX": "48", "UT": "49",
    "VT": "50", "VA": "51", "WA": "53", "WV": "54", "WI": "55",
    "WY": "56",
}

# Approximate center coordinates per state (from Census Bureau geographic centers)
STATE_COORDINATES = {
    "AL": (32.8, -86.8), "AK": (64.0, -153.0), "AZ": (34.3, -111.7),
    "AR": (34.8, -92.2), "CA": (37.2, -119.5), "CO": (39.0, -105.5),
    "CT": (41.6, -72.7), "DE": (39.0, -75.5), "DC": (38.9, -77.0),
    "FL": (28.6, -82.4), "GA": (32.7, -83.4), "HI": (20.8, -156.3),
    "ID": (44.4, -114.6), "IL": (40.0, -89.2), "IN": (39.9, -86.3),
    "IA": (42.0, -93.5), "KS": (38.5, -98.3), "KY": (37.8, -85.3),
    "LA": (31.0, -91.9), "ME": (45.4, -69.2), "MD": (39.0, -76.8),
    "MA": (42.3, -71.8), "MI": (44.3, -84.6), "MN": (46.3, -94.3),
    "MS": (32.7, -89.7), "MO": (38.4, -92.5), "MT": (47.0, -109.6),
    "NE": (41.5, -99.8), "NV": (39.3, -116.6), "NH": (43.7, -71.6),
    "NJ": (40.1, -74.7), "NM": (34.4, -106.1), "NY": (42.9, -75.5),
    "NC": (35.5, -79.8), "ND": (47.4, -100.5), "OH": (40.4, -82.8),
    "OK": (35.6, -97.5), "OR": (44.0, -120.5), "PA": (40.9, -77.8),
    "RI": (41.7, -71.5), "SC": (33.9, -80.9), "SD": (44.4, -100.2),
    "TN": (35.9, -86.4), "TX": (31.5, -99.3), "UT": (39.3, -111.7),
    "VT": (44.1, -72.6), "VA": (37.5, -78.9), "WA": (47.4, -120.5),
    "WV": (38.6, -80.6), "WI": (44.6, -89.8), "WY": (43.0, -107.6),
}

# Generic county names for synthetic data generation (used for states not in COUNTY_DATA_BY_STATE)
SYNTHETIC_COUNTY_NAMES = [
    "Washington", "Jefferson", "Franklin", "Lincoln", "Madison",
    "Jackson", "Monroe", "Hamilton", "Adams", "Marshall",
    "Grant", "Harrison", "Clark", "Union", "Marion",
    "Warren", "Lawrence", "Douglas", "Morgan", "Crawford",
]

# Generic city names for synthetic fallback
SYNTHETIC_CITY_NAMES = [
    "Springfield", "Riverside", "Fairview", "Georgetown", "Oakland",
    "Greenville", "Burlington", "Midway", "Salem", "Chester",
    "Clayton", "Ashland", "Dover", "Clifton", "Troy",
]

# Counties by state with SSA codes, FIPS codes, and county classification
COUNTY_DATA_BY_STATE = {
    # SSA codes from NBER SSA-FIPS crosswalk (ssa_fips_state_county_2024.csv)
    # WI: SSA state=52, FIPS state=55
    # CBSA/Metro-Micro from OMB CBSA Delineation Files
    "WI": {
        "Milwaukee":    {"ssa": "52390", "fips": "55079", "class": "Metro",  "lat": (42.9, 43.2), "lon": (-88.1, -87.8)},
        "Dane":         {"ssa": "52120", "fips": "55025", "class": "Metro",  "lat": (42.9, 43.3), "lon": (-89.6, -89.1)},
        "Waukesha":     {"ssa": "52660", "fips": "55133", "class": "Metro",  "lat": (42.8, 43.1), "lon": (-88.6, -88.1)},
        "Brown":        {"ssa": "52040", "fips": "55009", "class": "Metro",  "lat": (44.3, 44.7), "lon": (-88.3, -87.8)},
        "Racine":       {"ssa": "52500", "fips": "55101", "class": "Metro",  "lat": (42.6, 42.8), "lon": (-88.0, -87.7)},
        "Outagamie":    {"ssa": "52430", "fips": "55087", "class": "Metro",  "lat": (44.2, 44.6), "lon": (-88.7, -88.2)},
        "Winnebago":    {"ssa": "52690", "fips": "55139", "class": "Metro",  "lat": (43.9, 44.2), "lon": (-88.8, -88.4)},
        "Kenosha":      {"ssa": "52290", "fips": "55059", "class": "Metro",  "lat": (42.5, 42.7), "lon": (-88.1, -87.8)},
        "Rock":         {"ssa": "52520", "fips": "55105", "class": "Metro",  "lat": (42.5, 42.8), "lon": (-89.3, -88.8)},
        "Marathon":     {"ssa": "52360", "fips": "55073", "class": "Metro",  "lat": (44.7, 45.2), "lon": (-90.0, -89.3)},
        "Sheboygan":    {"ssa": "52580", "fips": "55117", "class": "Metro",  "lat": (43.5, 43.9), "lon": (-88.0, -87.7)},
        "La Crosse":    {"ssa": "52310", "fips": "55063", "class": "Metro",  "lat": (43.7, 44.0), "lon": (-91.4, -90.9)},
        "Eau Claire":   {"ssa": "52170", "fips": "55035", "class": "Metro",  "lat": (44.6, 44.9), "lon": (-91.3, -90.8)},
        "Washington":   {"ssa": "52650", "fips": "55131", "class": "Metro",  "lat": (43.3, 43.5), "lon": (-88.3, -88.0)},
        "Dodge":        {"ssa": "52130", "fips": "55027", "class": "Micro",  "lat": (43.3, 43.6), "lon": (-89.0, -88.6)},
        "Wood":         {"ssa": "52700", "fips": "55141", "class": "Micro",  "lat": (44.3, 44.6), "lon": (-90.2, -89.7)},
        "Bayfield":     {"ssa": "52030", "fips": "55007", "class": "Rural",  "lat": (46.3, 47.0), "lon": (-91.5, -90.6)},
        "Iron":         {"ssa": "52250", "fips": "55051", "class": "CEAC",   "lat": (46.1, 46.6), "lon": (-90.5, -89.9)},
        "Florence":     {"ssa": "52180", "fips": "55037", "class": "Rural",  "lat": (45.8, 46.1), "lon": (-88.6, -88.0)},
        "Menominee":    {"ssa": "52381", "fips": "55078", "class": "CEAC",   "lat": (44.8, 45.1), "lon": (-88.8, -88.5)},
    },
    # SSA codes from NBER SSA-FIPS crosswalk (ssa_fips_state_county_2024.csv)
    # TX: SSA state=45, FIPS state=48
    # CBSA/Metro-Micro from OMB CBSA Delineation Files
    "TX": {
        "Harris":      {"ssa": "45610", "fips": "48201", "class": "Metro",  "lat": (29.7, 30.1), "lon": (-95.8, -95.0)},
        "Dallas":      {"ssa": "45390", "fips": "48113", "class": "Metro",  "lat": (32.6, 33.0), "lon": (-97.0, -96.5)},
        "Tarrant":     {"ssa": "45910", "fips": "48439", "class": "Metro",  "lat": (32.6, 32.9), "lon": (-97.5, -97.0)},
        "Bexar":       {"ssa": "45130", "fips": "48029", "class": "Metro",  "lat": (29.2, 29.7), "lon": (-98.8, -98.3)},
        "Travis":      {"ssa": "45940", "fips": "48453", "class": "Metro",  "lat": (30.1, 30.5), "lon": (-98.0, -97.5)},
        "Collin":      {"ssa": "45310", "fips": "48085", "class": "Metro",  "lat": (33.1, 33.5), "lon": (-96.8, -96.3)},
        "Denton":      {"ssa": "45410", "fips": "48121", "class": "Metro",  "lat": (33.0, 33.4), "lon": (-97.3, -96.8)},
        "El Paso":     {"ssa": "45480", "fips": "48141", "class": "Metro",  "lat": (31.6, 32.0), "lon": (-106.6, -106.2)},
        "Hidalgo":     {"ssa": "45650", "fips": "48215", "class": "Metro",  "lat": (26.1, 26.6), "lon": (-98.5, -97.9)},
        "Fort Bend":   {"ssa": "45530", "fips": "48157", "class": "Metro",  "lat": (29.4, 29.7), "lon": (-95.9, -95.5)},
        "Williamson":  {"ssa": "45970", "fips": "48491", "class": "Metro",  "lat": (30.5, 30.9), "lon": (-97.8, -97.3)},
        "Montgomery":  {"ssa": "45801", "fips": "48339", "class": "Metro",  "lat": (30.2, 30.6), "lon": (-95.7, -95.2)},
        "Lubbock":     {"ssa": "45770", "fips": "48303", "class": "Metro",  "lat": (33.3, 33.7), "lon": (-102.0, -101.6)},
        "Cameron":     {"ssa": "45240", "fips": "48061", "class": "Metro",  "lat": (25.8, 26.2), "lon": (-97.7, -97.1)},
        "Nueces":      {"ssa": "45830", "fips": "48355", "class": "Metro",  "lat": (27.6, 28.0), "lon": (-97.6, -97.1)},
        "Brewster":    {"ssa": "45200", "fips": "48043", "class": "Rural",  "lat": (29.5, 30.5), "lon": (-103.9, -103.0)},
        "Loving":      {"ssa": "45762", "fips": "48301", "class": "CEAC",   "lat": (31.8, 32.1), "lon": (-104.2, -103.9)},
        "Presidio":    {"ssa": "45861", "fips": "48377", "class": "Rural",  "lat": (29.5, 30.5), "lon": (-104.9, -104.0)},
    },
}

CITIES_BY_COUNTY = {
    # Wisconsin
    "Milwaukee": ["Milwaukee", "West Allis", "Wauwatosa", "Greenfield", "Oak Creek"],
    "Dane": ["Madison", "Sun Prairie", "Fitchburg", "Middleton", "Verona"],
    "Waukesha": ["Waukesha", "Brookfield", "New Berlin", "Menomonee Falls", "Muskego"],
    "Brown": ["Green Bay", "De Pere", "Ashwaubenon", "Howard", "Allouez"],
    "Racine": ["Racine", "Mount Pleasant", "Caledonia", "Burlington", "Sturtevant"],
    "Outagamie": ["Appleton", "Kaukauna", "Little Chute", "Greenville", "Seymour"],
    "Winnebago": ["Oshkosh", "Neenah", "Menasha", "Omro", "Winneconne"],
    "Kenosha": ["Kenosha", "Pleasant Prairie", "Salem", "Twin Lakes", "Paddock Lake"],
    "Rock": ["Janesville", "Beloit", "Milton", "Edgerton", "Evansville"],
    "Marathon": ["Wausau", "Rothschild", "Schofield", "Mosinee", "Marathon City"],
    "Sheboygan": ["Sheboygan", "Sheboygan Falls", "Plymouth", "Kohler", "Elkhart Lake"],
    "La Crosse": ["La Crosse", "Onalaska", "Holmen", "West Salem", "Bangor"],
    "Eau Claire": ["Eau Claire", "Altoona", "Fall Creek", "Augusta", "Fairchild"],
    "Washington": ["West Bend", "Hartford", "Germantown", "Slinger", "Jackson"],
    "Dodge": ["Beaver Dam", "Waupun", "Horicon", "Juneau", "Mayville"],
    "Wood": ["Wisconsin Rapids", "Marshfield", "Nekoosa", "Pittsville", "Vesper"],
    "Bayfield": ["Washburn", "Bayfield", "Cable", "Iron River"],
    "Iron": ["Hurley", "Mercer", "Montreal"],
    "Florence": ["Florence", "Long Lake", "Fence"],
    "Menominee": ["Keshena", "Neopit", "Middle Village"],
    # Texas
    "Harris": ["Houston", "Pasadena", "Baytown", "Katy", "Spring"],
    "Dallas": ["Dallas", "Irving", "Garland", "Richardson", "Mesquite"],
    "Tarrant": ["Fort Worth", "Arlington", "Grapevine", "Southlake", "Bedford"],
    "Bexar": ["San Antonio", "Converse", "Live Oak", "Universal City", "Helotes"],
    "Travis": ["Austin", "Pflugerville", "Lakeway", "Bee Cave", "Rollingwood"],
    "Collin": ["Plano", "McKinney", "Frisco", "Allen", "Wylie"],
    "Denton": ["Denton", "Lewisville", "Flower Mound", "Little Elm", "Corinth"],
    "El Paso": ["El Paso", "Socorro", "Horizon City", "Anthony", "Canutillo"],
    "Hidalgo": ["McAllen", "Edinburg", "Mission", "Pharr", "Weslaco"],
    "Fort Bend": ["Sugar Land", "Missouri City", "Rosenberg", "Richmond", "Stafford"],
    "Williamson": ["Round Rock", "Cedar Park", "Georgetown", "Leander", "Hutto"],
    "Montgomery": ["Conroe", "The Woodlands", "Magnolia", "Willis", "New Caney"],
    "Lubbock": ["Lubbock", "Wolfforth", "Slaton", "Shallowater", "Idalou"],
    "Cameron": ["Brownsville", "Harlingen", "San Benito", "Los Fresnos", "La Feria"],
    "Nueces": ["Corpus Christi", "Robstown", "Port Aransas", "Calallen", "Flour Bluff"],
    "Brewster": ["Alpine", "Marathon", "Terlingua"],
    "Loving": ["Mentone"],
    "Presidio": ["Marfa", "Presidio", "Shafter"],
}

SPECIALTY_CODES = {
    "Cardiology":       {"code": "007", "desc": "Cardiology",                        "formula": "TimeAndDistance"},
    "Dermatology":      {"code": "011", "desc": "Dermatology",                       "formula": "TimeAndDistance"},
    "Endocrinology":    {"code": "014", "desc": "Endocrinology",                     "formula": "TimeAndDistance"},
    "Family Medicine":  {"code": "038", "desc": "Family Medicine/General Practice",   "formula": "TimeAndDistance"},
    "Gastroenterology": {"code": "019", "desc": "Gastroenterology",                  "formula": "TimeAndDistance"},
    "Internal Medicine":{"code": "046", "desc": "Internal Medicine",                  "formula": "TimeAndDistance"},
    "Neurology":        {"code": "062", "desc": "Neurology",                         "formula": "TimeAndDistance"},
    "OB/GYN":           {"code": "065", "desc": "Obstetrics & Gynecology",           "formula": "TimeAndDistance"},
    "Oncology":         {"code": "066", "desc": "Oncology - Medical",                "formula": "TimeAndDistance"},
    "Ophthalmology":    {"code": "067", "desc": "Ophthalmology",                     "formula": "TimeAndDistance"},
    "Orthopedics":      {"code": "069", "desc": "Orthopedic Surgery",                "formula": "TimeAndDistance"},
    "Pediatrics":       {"code": "076", "desc": "Pediatrics",                        "formula": "TimeAndDistance"},
    "Psychiatry":       {"code": "086", "desc": "Psychiatry",                        "formula": "TimeAndDistance"},
    "Pulmonology":      {"code": "088", "desc": "Pulmonary Disease",                 "formula": "TimeAndDistance"},
    "Urology":          {"code": "098", "desc": "Urology",                           "formula": "TimeAndDistance"},
}

TAXONOMY_BY_SPECIALTY = {
    "Cardiology":       ["207RC0000X", "207RI0011X", "207RC0001X"],
    "Dermatology":      ["207N00000X", "207NI0002X", "207ND0101X"],
    "Endocrinology":    ["207RE0101X", "207RG0100X"],
    "Family Medicine":  ["207Q00000X", "207QA0505X", "207QA0000X"],
    "Gastroenterology": ["207RG0300X", "204C00000X"],
    "Internal Medicine":["207R00000X", "207RA0000X"],
    "Neurology":        ["2084N0400X", "2084N0402X"],
    "OB/GYN":           ["207V00000X", "207VG0400X", "207VX0201X"],
    "Oncology":         ["207RX0202X", "207VX0000X"],
    "Ophthalmology":    ["207W00000X", "207WX0200X"],
    "Orthopedics":      ["207X00000X", "207XS0114X", "207XS0106X"],
    "Pediatrics":       ["208000000X", "2080P0006X"],
    "Psychiatry":       ["2084P0800X", "2084P0802X", "2084P0804X"],
    "Pulmonology":      ["207RP1001X", "207RT0003X"],
    "Urology":          ["208800000X", "2088P0231X"],
}

FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael",
    "Linda", "David", "Elizabeth", "William", "Barbara", "Richard", "Susan",
    "Joseph", "Jessica", "Thomas", "Sarah", "Christopher", "Karen",
    "Anil", "Priya", "Wei", "Mei", "Ahmed", "Fatima", "Carlos", "Maria",
    "Raj", "Lakshmi", "Hiroshi", "Yuki", "Omar", "Amira", "Diego", "Sofia",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Patel", "Kumar", "Chen", "Wang", "Ali", "Kim", "Singh", "Nguyen",
    "Shah", "Gupta", "Lee", "Park", "Santos", "Rivera", "Morales", "Reyes",
]

STREET_NAMES = [
    "Main St", "Oak Ave", "Elm Blvd", "Park Dr", "Cedar Ln",
    "Maple Rd", "Pine St", "Medical Center Blvd", "Hospital Dr",
    "Health Pkwy", "Clinic Way", "University Ave", "Research Blvd",
    "Professional Dr", "Healthcare Way", "Wellness Ln",
]

FACILITY_NAMES = [
    "Memorial Medical Center", "St. Joseph's Hospital", "Baptist Health Clinic",
    "Methodist Healthcare System", "University Medical Associates",
    "Texas Health Partners", "Baylor Scott & White Clinic", "HCA Healthcare Center",
    "Community Health Network", "Seton Medical Group", "MD Anderson Satellite Clinic",
    "Children's Hospital Network", "Presbyterian Medical Associates",
    "Covenant Health Clinic", "Valley Baptist Medical Group",
    "Christus Health Center", "Parkland Community Clinic",
]

PREFIXES = ["Dr.", "Dr.", "Dr.", ""]
SUFFIXES = ["MD", "DO", "MD", "MD, FACC", "MD, FACS", "DO, FACEP", ""]
MIDDLE_NAMES = [
    "A.", "B.", "C.", "D.", "E.", "J.", "K.", "L.", "M.", "N.", "P.", "R.", "S.", "T.",
    "Ann", "Lee", "Marie", "James", "Ray", "Jean", "Lynn", "Rose", "",
]

ORGANIZATION_NAMES_BY_STATE = {
    "WI": [
        "Froedtert Hospital", "UW Health", "Aurora Health Care",
        "Marshfield Clinic Health System", "Gundersen Health System",
        "Ascension Wisconsin", "Bellin Health", "ThedaCare",
        "ProHealth Care", "Advocate Aurora Health",
        "SSM Health Wisconsin", "Aspirus Health",
        "Mayo Clinic Health System", "Prevea Health",
        "Children's Wisconsin", "Medical College of Wisconsin",
        "Mercy Health System", "Columbia St. Mary's",
        "Waukesha Memorial Hospital", "Meriter Hospital",
    ],
    "TX": [
        "Memorial Hermann Health System", "Baylor Scott & White Health",
        "Texas Health Resources", "Methodist Hospital System",
        "MD Anderson Cancer Center", "UT Southwestern Medical Center",
        "HCA Houston Healthcare", "Christus Health",
        "Parkland Health & Hospital System", "Seton Healthcare Family",
        "Valley Baptist Medical Center", "Covenant Health System",
        "Shannon Medical Center", "Driscoll Health System",
        "Cook Children's Medical Center", "JPS Health Network",
        "University Health System", "Harris Health System",
        "El Paso Children's Hospital", "Medical City Healthcare",
    ],
}
# Fallback for states without specific organizations
DEFAULT_ORGANIZATION_NAMES = [
    "Regional Medical Center", "Community Health System",
    "University Hospital", "Memorial Hospital",
    "St. Mary's Medical Center", "Children's Hospital",
    "Mercy Health System", "Providence Health",
    "HCA Healthcare", "Ascension Health",
]

CONTRACT_IDS = [
    "H0028", "H0351", "H1036", "H3204", "H4590", "H5521", "H6800",
    "H7917", "H8145", "H9382", "R0142", "R2019", "R4501", "S2468", "S5710",
]

SOURCE_SYSTEMS = ["CMS NPPES", "State Registry", "Credentialing DB", "Manual Entry", "Provider Portal"]

RACES = ["White", "Black or African American", "Asian", "Hispanic or Latino",
         "American Indian or Alaska Native", "Native Hawaiian or Pacific Islander", "Two or More Races"]

ETHNICITIES = ["Hispanic or Latino", "Not Hispanic or Latino"]

LANGUAGES = ["English", "Spanish", "Mandarin", "Vietnamese", "Hindi", "Korean",
             "Tagalog", "Arabic", "French", "Portuguese", "German", "Urdu"]


# ============================================================================
# Synthetic County Generation (fallback for states not in COUNTY_DATA_BY_STATE)
# ============================================================================

def _generate_synthetic_counties(state, num_counties, rng):
    """Generate synthetic county data for states not in the hardcoded lookup.
    Uses SSA/FIPS state codes, approximate coordinates, and realistic classifications.
    Returns a dict in the same format as COUNTY_DATA_BY_STATE entries."""
    ssa_prefix = SSA_STATE_CODES.get(state, "99")
    fips_prefix = FIPS_STATE_CODES.get(state, "99")
    center = STATE_COORDINATES.get(state, (39.8, -98.6))  # geographic center of US

    county_names = rng.sample(SYNTHETIC_COUNTY_NAMES, min(num_counties, len(SYNTHETIC_COUNTY_NAMES)))
    if num_counties > len(SYNTHETIC_COUNTY_NAMES):
        for i in range(num_counties - len(SYNTHETIC_COUNTY_NAMES)):
            county_names.append(f"County_{i+1:03d}")

    # Assign classifications: ~60% Metro, ~20% Micro, ~15% Rural, ~5% CEAC
    classifications = []
    for i in range(len(county_names)):
        r = rng.random()
        if r < 0.60:
            classifications.append("Metro")
        elif r < 0.80:
            classifications.append("Micro")
        elif r < 0.95:
            classifications.append("Rural")
        else:
            classifications.append("CEAC")

    counties = {}
    for i, (name, cls) in enumerate(zip(county_names, classifications)):
        ssa_county = f"{(i + 1) * 10:03d}"  # 010, 020, 030, ...
        fips_county = f"{(i * 2 + 1):03d}"  # 001, 003, 005, ...
        lat_center = center[0] + rng.uniform(-2.0, 2.0)
        lon_center = center[1] + rng.uniform(-2.0, 2.0)
        counties[name] = {
            "ssa": f"{ssa_prefix}{ssa_county}",
            "fips": f"{fips_prefix}{fips_county}",
            "class": cls,
            "lat": (round(lat_center - 0.3, 1), round(lat_center + 0.3, 1)),
            "lon": (round(lon_center - 0.3, 1), round(lon_center + 0.3, 1)),
        }

    # Also register synthetic cities for these counties
    for name in county_names:
        if name not in CITIES_BY_COUNTY:
            CITIES_BY_COUNTY[name] = rng.sample(
                SYNTHETIC_CITY_NAMES, min(4, len(SYNTHETIC_CITY_NAMES))
            )

    return counties


# ============================================================================
# Data Generation
# ============================================================================

def generate_all_data(cfg: dict) -> dict:
    """Returns dict with qes_na, qes_providers, niq_na, niq_providers DataFrames.
    Works for any US state: uses verified public data for TX/WI, generates
    synthetic county data for all other states."""
    mock_cfg = cfg.get("mock", {})
    seed = mock_cfg.get("seed", 42)
    num_counties = mock_cfg.get("num_counties", 15)
    num_specialties = mock_cfg.get("num_specialties", 10)
    prov_range = mock_cfg.get("num_providers_range", [5, 50])
    mismatch_rate = mock_cfg.get("mismatch_rate", 0.20)
    qes_only_rate = mock_cfg.get("qes_only_rate", 0.05)
    niq_only_rate = mock_cfg.get("niq_only_rate", 0.05)
    zero_serving_rate = mock_cfg.get("zero_serving_rate", 0.03)
    project_name = mock_cfg.get("project_name", f"{cfg['state']}_NA_2026")
    filing_types = mock_cfg.get("filing_types", ["SBE", "QHP"])
    lob_types = mock_cfg.get("lob_types", ["Commercial", "Medicare", "Medicaid"])
    facility_rate = mock_cfg.get("facility_rate", 0.15)
    state = cfg["state"]
    state_name = STATE_NAMES.get(state, state)

    rng = random.Random(seed)
    np.random.seed(seed)

    state_counties = COUNTY_DATA_BY_STATE.get(state, {})
    if not state_counties:
        if state not in STATE_NAMES:
            raise ValueError(f"Unknown state code: {state}. Use a valid 2-letter US state abbreviation.")
        print(f"  [info] No verified county data for {state}. Generating synthetic data...")
        state_counties = _generate_synthetic_counties(state, num_counties + 5, rng)
    county_names = list(state_counties.keys())
    counties = rng.sample(county_names, min(num_counties, len(county_names)))
    zip_lo, zip_hi = ZIP_RANGES_BY_STATE.get(state, (10000, 99999))
    specialty_names = list(SPECIALTY_CODES.keys())
    specialties = rng.sample(specialty_names, min(num_specialties, len(specialty_names)))

    qes_na_rows, qes_prov_rows = [], []
    niq_na_rows, niq_prov_rows = [], []

    for county in counties:
        county_info = state_counties[county]
        ssa_code = county_info["ssa"]
        fips_code = county_info["fips"]
        county_class = county_info["class"]

        for specialty in specialties:
            spec_info = SPECIALTY_CODES[specialty]
            spec_code = spec_info["code"]
            spec_desc = spec_info["desc"]
            spec_formula = spec_info["formula"]

            num_providers = rng.randint(prov_range[0], prov_range[1])
            membership_count = rng.randint(500, 50000)
            coverage_pct = round(rng.uniform(90.0, 100.0), 2)
            members_with_access = int(membership_count * coverage_pct / 100)
            access_met = "Y" if coverage_pct >= 90.0 else "N"
            required_providers = rng.randint(1, 10)
            servicing_providers = num_providers
            servicing_method = rng.choice(["Providers", "Locations"])
            met_servicing = "Y" if servicing_providers >= required_providers else "N"
            met_overall = "Y" if access_met == "Y" and met_servicing == "Y" else "N"
            market_serving = rng.randint(10, 500)
            pct_of_market = round(rng.uniform(5.0, 80.0), 2)

            # Determine row fate
            fate_roll = rng.random()
            is_qes_only = fate_roll < qes_only_rate
            is_niq_only = not is_qes_only and fate_roll < (qes_only_rate + niq_only_rate)
            is_zero_serving = not is_qes_only and not is_niq_only and rng.random() < zero_serving_rate
            is_mismatch = not is_qes_only and not is_niq_only and not is_zero_serving and rng.random() < mismatch_rate

            # Generate providers (shared base for both QES and NIQ when in both)
            providers = _generate_providers_base(
                state, county, specialty, num_providers, rng, county_info, facility_rate
            )

            # Handle zero serving case
            if is_zero_serving:
                servicing_providers = 0
                met_servicing = "N"
                met_overall = "N"
                providers = []

            # --- QES row ---
            if not is_niq_only:
                qes_na_rows.append({
                    "Project Name": project_name,
                    "CountySSA": ssa_code,
                    "FIPS County": fips_code,
                    "County Name": county,
                    "County Class (Rural/Metro/Micro/CEAC)": county_class,
                    "State": state,
                    "State Name": state_name,
                    "County Status": "Active",
                    "Specialty Group Code": spec_code,
                    "Specialty Group Name": spec_desc,
                    "Membership Count": membership_count,
                    "Membership": membership_count,
                    "Calculation Method": spec_formula,
                    "Servicing Count Method": servicing_method,
                    "Members with Access": members_with_access,
                    "% members with Access": coverage_pct,
                    "Access Met (Y/N)": access_met,
                    "Required Providers count": required_providers,
                    "Servicing Providers count": servicing_providers,
                    "Met Servicing": met_servicing,
                    "Met Overall": met_overall,
                    "Market Serving": market_serving,
                    "% Of Market": pct_of_market,
                })
                for p in providers:
                    qes_prov_rows.append(_format_qes_provider(p, state, county, spec_code, spec_desc))

            # --- NIQ row ---
            if not is_qes_only:
                niq_coverage = coverage_pct
                niq_providers_count = servicing_providers
                niq_members = membership_count
                niq_covered = members_with_access
                niq_status = "Met" if access_met == "Y" else "Not Met"
                niq_provs = list(providers)

                if is_mismatch:
                    mtype = rng.choice(["coverage_higher", "coverage_lower", "provider_diff", "member_diff"])
                    if mtype == "coverage_higher":
                        niq_coverage = min(100.0, round(coverage_pct + rng.uniform(1.0, 8.0), 2))
                    elif mtype == "coverage_lower":
                        niq_coverage = max(85.0, round(coverage_pct - rng.uniform(1.0, 8.0), 2))
                    elif mtype == "provider_diff":
                        delta = rng.choice([-2, -1, 1, 2, 3])
                        niq_providers_count = max(0, servicing_providers + delta)
                        if delta > 0:
                            extras = _generate_providers_base(
                                state, county, specialty, delta, rng, county_info, facility_rate
                            )
                            niq_provs.extend(extras)
                        elif delta < 0:
                            niq_provs = niq_provs[:max(0, len(niq_provs) + delta)]
                    elif mtype == "member_diff":
                        niq_members = membership_count + rng.randint(-2000, 2000)
                        niq_covered = int(niq_members * niq_coverage / 100)

                    niq_status = "Met" if niq_coverage >= 90.0 else "Not Met"

                niq_na_rows.append({
                    "Project": project_name,
                    "LOB": rng.choice(lob_types),
                    "state": state,
                    "countSSACode": ssa_code,
                    "county": county,
                    "zip": f"{rng.randint(zip_lo, zip_hi):05d}",
                    "specialty_code": spec_code,
                    "specialty_group_name": spec_desc,
                    "specialty_formula": spec_formula,
                    "total_members": niq_members,
                    "covered_members": niq_covered,
                    "threshold": required_providers,
                    "provider_covering": niq_providers_count,
                    "accurate_covered_members": niq_covered,
                    "filing_type": rng.choice(filing_types),
                    "coverage_percentage": niq_coverage,
                    "coverage_status": niq_status,
                })
                for p in niq_provs:
                    niq_prov_rows.append(_format_niq_provider(p, state, county, spec_code, spec_desc))

    return {
        "qes_na": pd.DataFrame(qes_na_rows),
        "qes_providers": pd.DataFrame(qes_prov_rows),
        "niq_na": pd.DataFrame(niq_na_rows),
        "niq_providers": pd.DataFrame(niq_prov_rows),
    }


ZIP_RANGES_BY_STATE = {
    "AL": (35000, 36999), "AK": (99500, 99999), "AZ": (85000, 86599),
    "AR": (71600, 72999), "CA": (90000, 96699), "CO": (80000, 81699),
    "CT": (6000, 6999),   "DE": (19700, 19999), "DC": (20000, 20099),
    "FL": (32000, 34999), "GA": (30000, 31999), "HI": (96700, 96899),
    "ID": (83200, 83899), "IL": (60000, 62999), "IN": (46000, 47999),
    "IA": (50000, 52899), "KS": (66000, 67999), "KY": (40000, 42799),
    "LA": (70000, 71499), "ME": (3900, 4999),   "MD": (20600, 21999),
    "MA": (1000, 2799),   "MI": (48000, 49999), "MN": (55000, 56799),
    "MS": (38600, 39799), "MO": (63000, 65899), "MT": (59000, 59999),
    "NE": (68000, 69399), "NV": (88900, 89899), "NH": (3000, 3899),
    "NJ": (7000, 8999),   "NM": (87000, 88499), "NY": (10000, 14999),
    "NC": (27000, 28999), "ND": (58000, 58899), "OH": (43000, 45999),
    "OK": (73000, 74999), "OR": (97000, 97999), "PA": (15000, 19699),
    "RI": (2800, 2999),   "SC": (29000, 29999), "SD": (57000, 57799),
    "TN": (37000, 38599), "TX": (70000, 79999), "UT": (84000, 84799),
    "VT": (5000, 5999),   "VA": (20100, 24699), "WA": (98000, 99499),
    "WV": (24700, 26899), "WI": (53000, 54999), "WY": (82000, 83199),
}


def _generate_providers_base(state, county, specialty, count, rng, county_info, facility_rate):
    """Generate base provider data (shared structure before formatting to QES/NIQ columns)."""
    cities = CITIES_BY_COUNTY.get(county, [county])
    lat_range = county_info.get("lat", (30.0, 31.0))
    lon_range = county_info.get("lon", (-97.0, -96.0))
    taxonomies = TAXONOMY_BY_SPECIALTY.get(specialty, ["000000000X"])
    zip_lo, zip_hi = ZIP_RANGES_BY_STATE.get(state, (10000, 99999))

    providers = []
    for _ in range(count):
        is_facility = rng.random() < facility_rate
        first = rng.choice(FIRST_NAMES)
        middle = rng.choice(MIDDLE_NAMES)
        last = rng.choice(LAST_NAMES)
        prefix = rng.choice(PREFIXES)
        suffix = rng.choice(SUFFIXES)
        gender = rng.choice(["M", "F"])

        org_names = ORGANIZATION_NAMES_BY_STATE.get(state, DEFAULT_ORGANIZATION_NAMES)
        org_name = rng.choice(org_names)
        contract_id = rng.choice(CONTRACT_IDS)

        providers.append({
            "npi": str(rng.randint(1000000000, 9999999999)),
            "tax_id": str(rng.randint(100000000, 999999999)),
            "is_facility": is_facility,
            "facility_name": rng.choice(FACILITY_NAMES) if is_facility else "",
            "first_name": "" if is_facility else first,
            "last_name": "" if is_facility else last,
            "prefix": "" if is_facility else prefix,
            "middle": "" if is_facility else middle,
            "suffix": "" if is_facility else suffix,
            "gender": "" if is_facility else gender,
            "entity_type": "Organization" if is_facility else "Individual",
            "address": f"{rng.randint(100, 9999)} {rng.choice(STREET_NAMES)}",
            "address2": rng.choice(["", "", "", f"Suite {rng.randint(100, 999)}", f"Bldg {rng.choice(['A','B','C'])}"]),
            "city": rng.choice(cities),
            "zip": f"{rng.randint(zip_lo, zip_hi):05d}",
            "latitude": round(rng.uniform(lat_range[0], lat_range[1]), 6),
            "longitude": round(rng.uniform(lon_range[0], lon_range[1]), 6),
            "taxonomy": rng.choice(taxonomies),
            "phone": f"{rng.randint(200, 999)}-{rng.randint(200, 999)}-{rng.randint(1000, 9999)}",
            "accepting": rng.choice(["Yes", "Yes", "Yes", "No"]),
            "organization": org_name,
            "contract": contract_id,
            "source": rng.choice(SOURCE_SYSTEMS),
            "race": rng.choice(RACES),
            "ethnicity": rng.choice(ETHNICITIES),
            "language": rng.choice(["English", "English", "English", "Spanish"]) if not is_facility else "",
            "board_certified": rng.choice(["Y", "Y", "Y", "N"]) if not is_facility else "",
        })
    return providers


def _format_qes_provider(p, state, county, spec_code, spec_desc):
    """Format base provider dict into QES column names."""
    return {
        "NPI": p["npi"],
        "TaxID": p["tax_id"],
        "Specialty Group Code": spec_code,
        "Specialty Group Desc": spec_desc,
        "ServicingState": state,
        "ServicingCounty": county,
        "Address": p["address"],
        "Address2": p["address2"],
        "City": p["city"],
        "State": state,
        "Zip": p["zip"],
        "Latitude": p["latitude"],
        "Longitude": p["longitude"],
        "EntityType": p["entity_type"],
        "Facility Name": p["facility_name"],
        "Organization": p["organization"],
        "lastName": p["last_name"],
        "FirstName": p["first_name"],
        "Taxonomy": p["taxonomy"],
        "Phone": p["phone"],
        "TIN": p["tax_id"],
        "Prefix": p["prefix"],
        "First": p["first_name"],
        "Middle": p["middle"],
        "Last": p["last_name"],
        "Suffix": p["suffix"],
        "Gender": p["gender"],
        "Race": p["race"],
        "Ethnicity": p["ethnicity"],
        "Language": p["language"],
        "Board Certified": p["board_certified"],
        "Accepting Patients": p["accepting"],
        "Contract": p["contract"],
        "Source": p["source"],
    }


def _format_niq_provider(p, state, county, spec_code, spec_desc):
    """Format base provider dict into NIQ column names (lowercase, underscored)."""
    return {
        "npi": p["npi"],
        "tax_id": p["tax_id"],
        "specialty_group_code": spec_code,
        "specialty_group_desc": spec_desc,
        "servicing_state": state,
        "servicing_county": county,
        "address": p["address"],
        "address2": p["address2"],
        "city": p["city"],
        "state": state,
        "zip": p["zip"],
        "latitude": p["latitude"],
        "longitude": p["longitude"],
        "entity_type": p["entity_type"],
        "facility_name": p["facility_name"],
        "organization": p["organization"],
        "last_name": p["last_name"],
        "first_name": p["first_name"],
        "taxonomy": p["taxonomy"],
        "phone": p["phone"],
        "tin": p["tax_id"],
        "prefix": p["prefix"],
        "first": p["first_name"],
        "middle": p["middle"],
        "last": p["last_name"],
        "suffix": p["suffix"],
        "gender": p["gender"],
        "race": p["race"],
        "ethnicity": p["ethnicity"],
        "language": p["language"],
        "board_certified": p["board_certified"],
        "accepting_patients": p["accepting"],
        "contract": p["contract"],
        "source": p["source"],
    }


def save_qes_workbooks(data: dict, cfg: dict):
    """Save QES data as two separate Excel workbooks (simulating input files)."""
    qes_cfg = cfg["qes"]
    os.makedirs(os.path.dirname(qes_cfg["workbook1_path"]) or ".", exist_ok=True)
    data["qes_na"].to_excel(qes_cfg["workbook1_path"], index=False, sheet_name="Sheet1")
    data["qes_providers"].to_excel(qes_cfg["workbook2_path"], index=False, sheet_name="Sheet1")
    print(f"  [saved] QES Workbook-1: {qes_cfg['workbook1_path']} ({len(data['qes_na'])} rows)")
    print(f"  [saved] QES Workbook-2: {qes_cfg['workbook2_path']} ({len(data['qes_providers'])} rows)")


def save_niq_workbook(data: dict, cfg: dict):
    """Save NIQ data as a single Excel workbook with two sheets (simulating input)."""
    excel_cfg = cfg["niq"]["excel"]
    wb_path = excel_cfg["workbook_path"]
    na_sheet = excel_cfg.get("network_adequacy_sheet", "NetworkAdequacy")
    prov_sheet = excel_cfg.get("provider_detail_sheet", "ProviderDetail")

    os.makedirs(os.path.dirname(wb_path) or ".", exist_ok=True)
    with pd.ExcelWriter(wb_path, engine="openpyxl") as writer:
        data["niq_na"].to_excel(writer, index=False, sheet_name=na_sheet)
        data["niq_providers"].to_excel(writer, index=False, sheet_name=prov_sheet)

    print(f"  [saved] NIQ Workbook: {wb_path}")
    print(f"          Sheet '{na_sheet}': {len(data['niq_na'])} rows")
    print(f"          Sheet '{prov_sheet}': {len(data['niq_providers'])} rows")
