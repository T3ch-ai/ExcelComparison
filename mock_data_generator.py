"""
Generates realistic mock data for both QES (Excel) and NIQ (Excel) datasets.
Introduces controlled mismatches so the comparator has meaningful output.
Also generates the NIQ workbook with two sheets when source_type=mock.
"""

import random
import os
import pandas as pd
import numpy as np

COUNTIES_TX = [
    "Harris", "Dallas", "Tarrant", "Bexar", "Travis",
    "Collin", "Denton", "El Paso", "Hidalgo", "Fort Bend",
    "Williamson", "Montgomery", "Lubbock", "Cameron", "Nueces",
]

SPECIALTIES = [
    "Cardiology", "Dermatology", "Endocrinology", "Family Medicine",
    "Gastroenterology", "Internal Medicine", "Neurology", "OB/GYN",
    "Oncology", "Ophthalmology", "Orthopedics", "Pediatrics",
    "Psychiatry", "Pulmonology", "Urology",
]

FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael",
    "Linda", "David", "Elizabeth", "William", "Barbara", "Richard", "Susan",
    "Joseph", "Jessica", "Thomas", "Sarah", "Christopher", "Karen",
    "Anil", "Priya", "Wei", "Mei", "Ahmed", "Fatima", "Carlos", "Maria",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Patel", "Kumar", "Chen", "Wang", "Ali", "Kim", "Singh", "Nguyen",
]

STREET_NAMES = [
    "Main St", "Oak Ave", "Elm Blvd", "Park Dr", "Cedar Ln",
    "Maple Rd", "Pine St", "Medical Center Blvd", "Hospital Dr",
    "Health Pkwy", "Clinic Way", "University Ave",
]

CITIES_BY_COUNTY = {
    "Harris": ["Houston", "Pasadena", "Baytown"],
    "Dallas": ["Dallas", "Irving", "Garland"],
    "Tarrant": ["Fort Worth", "Arlington", "Grapevine"],
    "Bexar": ["San Antonio", "Converse", "Live Oak"],
    "Travis": ["Austin", "Pflugerville", "Lakeway"],
    "Collin": ["Plano", "McKinney", "Frisco"],
    "Denton": ["Denton", "Lewisville", "Flower Mound"],
    "El Paso": ["El Paso", "Socorro", "Horizon City"],
    "Hidalgo": ["McAllen", "Edinburg", "Mission"],
    "Fort Bend": ["Sugar Land", "Missouri City", "Rosenberg"],
    "Williamson": ["Round Rock", "Cedar Park", "Georgetown"],
    "Montgomery": ["Conroe", "The Woodlands", "Magnolia"],
    "Lubbock": ["Lubbock", "Wolfforth", "Slaton"],
    "Cameron": ["Brownsville", "Harlingen", "San Benito"],
    "Nueces": ["Corpus Christi", "Robstown", "Port Aransas"],
}


def generate_all_data(cfg: dict) -> dict:
    """Returns dict with qes_na, qes_providers, niq_na, niq_providers DataFrames."""
    mock_cfg = cfg.get("mock", {})
    seed = mock_cfg.get("seed", 42)
    num_counties = mock_cfg.get("num_counties", 8)
    num_specialties = mock_cfg.get("num_specialties", 6)
    prov_range = mock_cfg.get("num_providers_range", [3, 25])
    mismatch_rate = mock_cfg.get("mismatch_rate", 0.15)
    qes_only_rate = mock_cfg.get("qes_only_rate", 0.05)
    niq_only_rate = mock_cfg.get("niq_only_rate", 0.05)
    state = cfg["state"]

    rng = random.Random(seed)
    np.random.seed(seed)

    counties = rng.sample(COUNTIES_TX, min(num_counties, len(COUNTIES_TX)))
    specialties = rng.sample(SPECIALTIES, min(num_specialties, len(SPECIALTIES)))

    qes_na_rows, qes_prov_rows = [], []
    niq_na_rows, niq_prov_rows = [], []

    for county in counties:
        for specialty in specialties:
            num_providers = rng.randint(prov_range[0], prov_range[1])
            avg_distance = round(rng.uniform(1.5, 35.0), 2)
            meets_std = "Y" if num_providers >= 5 and avg_distance <= 30 else "N"
            member_count = rng.randint(500, 50000)

            fate_roll = rng.random()
            is_qes_only = fate_roll < qes_only_rate
            is_niq_only = not is_qes_only and fate_roll < (qes_only_rate + niq_only_rate)
            is_mismatch = not is_qes_only and not is_niq_only and rng.random() < mismatch_rate

            providers = _generate_providers(state, county, specialty, num_providers, rng)

            if not is_niq_only:
                qes_na_rows.append({
                    "State": state, "County_Name": county, "Specialty": specialty,
                    "Provider_Count": num_providers, "Meets_Standard": meets_std,
                    "Avg_Distance_Miles": avg_distance, "Member_Count": member_count,
                })
                for p in providers:
                    qes_prov_rows.append({
                        "State": state, "County_Name": county, "Specialty": specialty,
                        "Provider_NPI": p["npi"], "Provider_Name": p["name"],
                        "Provider_Address": p["address"], "Provider_City": p["city"],
                        "Provider_Zip": p["zip"], "Accepting_Patients": p["accepting"],
                    })

            if not is_qes_only:
                niq_count = num_providers
                niq_distance = avg_distance
                niq_meets = meets_std
                niq_members = member_count
                niq_provs = list(providers)

                if is_mismatch:
                    mtype = rng.choice(["count", "distance", "standard", "provider_diff"])
                    if mtype == "count":
                        delta = rng.choice([-2, -1, 1, 2, 3])
                        niq_count = max(0, num_providers + delta)
                        if delta > 0:
                            niq_provs.extend(_generate_providers(state, county, specialty, delta, rng))
                        elif delta < 0:
                            niq_provs = niq_provs[:niq_count]
                        niq_meets = "Y" if niq_count >= 5 and niq_distance <= 30 else "N"
                    elif mtype == "distance":
                        niq_distance = max(0.1, round(avg_distance + rng.uniform(-3.0, 5.0), 2))
                    elif mtype == "standard":
                        niq_meets = "N" if meets_std == "Y" else "Y"
                    elif mtype == "provider_diff":
                        if len(niq_provs) > 1:
                            idx = rng.randint(0, len(niq_provs) - 1)
                            niq_provs[idx] = _generate_providers(state, county, specialty, 1, rng)[0]

                niq_na_rows.append({
                    "state_code": state, "county_name": county, "specialty_type": specialty,
                    "provider_cnt": niq_count, "meets_standard_flag": niq_meets,
                    "avg_distance": niq_distance, "member_count": niq_members,
                })
                for p in niq_provs:
                    niq_prov_rows.append({
                        "state_code": state, "county_name": county, "specialty_type": specialty,
                        "provider_npi": p["npi"], "provider_name": p["name"],
                        "provider_address": p["address"], "provider_city": p["city"],
                        "provider_zip": p["zip"], "accepting_patients": p["accepting"],
                    })

    return {
        "qes_na": pd.DataFrame(qes_na_rows),
        "qes_providers": pd.DataFrame(qes_prov_rows),
        "niq_na": pd.DataFrame(niq_na_rows),
        "niq_providers": pd.DataFrame(niq_prov_rows),
    }


def _generate_providers(state, county, specialty, count, rng):
    cities = CITIES_BY_COUNTY.get(county, [county])
    providers = []
    for _ in range(count):
        providers.append({
            "npi": str(rng.randint(1000000000, 9999999999)),
            "name": f"Dr. {rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}",
            "address": f"{rng.randint(100, 9999)} {rng.choice(STREET_NAMES)}",
            "city": rng.choice(cities),
            "zip": str(rng.randint(70000, 79999)),
            "accepting": rng.choice(["Yes", "Yes", "Yes", "No"]),
        })
    return providers


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
