"""
Trading Economics /commodities table: display name (first column, bold)
↔ `tr[data-symbol]` tickers, grouped by section header (Energy, Metals, …).

Names and symbols follow the site HTML; if the table changes, refresh this file.
"""

from typing import Final

ENERGY_NAME_TO_TICKER: Final[dict[str, str]] = {
    "Crude Oil": "CL1:COM",
    "Brent": "CO1:COM",
    "Natural gas": "NG1:COM",
    "Gasoline": "XB1:COM",
    "Heating Oil": "HO1:COM",
    "Coal": "XAL1:COM",
    "TTF Gas": "NGEU:COM",
    "UK Gas": "NGUK:COM",
    "Ethanol": "DL1:COM",
    "Naphtha": "MOB:COM",
    "Propane": "PNL:COM",
    "Uranium": "UXA:COM",
    "Methanol": "CMA:COM",
    "Coking Coal": "DJM:COM",
    "LNG JKM": "LNGJKM:COM",
    "German Gas": "NGDE:COM",
    "Urals Oil": "URDB:COM",
}

METALS_NAME_TO_TICKER: Final[dict[str, str]] = {
    "Gold": "XAUUSD:CUR",
    "Silver": "XAGUSD:CUR",
    "Copper": "HG1:COM",
    "Steel": "JBP:COM",
    "Lithium": "LC:COM",
    "Iron Ore CNY": "IOE:COM",
    "Platinum": "XPTUSD:CUR",
    "Cobalt Hydroxide": "COH:COM",
    "HRC Steel": "HRC:COM",
    "Iron Ore": "SCO:COM",
    "Silicon": "SI:COM",
    "Scrap Steel": "SSC:COM",
    "Titanium": "TTSG:COM",
}

AGRICULTURAL_NAME_TO_TICKER: Final[dict[str, str]] = {
    "Soybeans": "S 1:COM",
    "Wheat": "W 1:COM",
    "Lumber": "LB1:COM",
    "Palm Oil": "PLO:COM",
    "Cheese": "CHE:COM",
    "Milk": "DA:COM",
    "Rubber": "JN1:COM",
    "Orange Juice": "JO1:COM",
    "Coffee": "KC1:COM",
    "Cotton": "CT1:COM",
    "Rice": "RR1:COM",
    "Canola": "RS1:COM",
    "Oat": "O 1:COM",
    "Wool": "OL1:COM",
    "Sugar": "SB1:COM",
    "Cocoa": "CC1:COM",
    "Tea": "TEA:COM",
    "Sunflower Oil": "SUNF:COM",
    "Rapeseed": "RSO:COM",
    "Barley": "BL1:COM",
    "Butter": "FABT:COM",
    "Potatoes": "FAPP:COM",
    "Corn": "C 1:COM",
}

INDUSTRIAL_NAME_TO_TICKER: Final[dict[str, str]] = {
    "Bitumen": "BIT:COM",
    "Cobalt": "LCO1:COM",
    "Lead": "LL1:COM",
    "Aluminum": "LMAHDS03:COM",
    "Tin": "LMSNDS03:COM",
    "Zinc": "LMZSDS03:COM",
    "Nickel": "LN1:COM",
    "Molybdenum": "MOLYBDEN:COM",
    "Palladium": "XPDUSD:CUR",
    "Rhodium": "XRH:COM",
    "Phosphorus": "PHO:COM",
    "Polyethylene": "POL:COM",
    "Polyvinyl": "PVC:COM",
    "Polypropylene": "PYL:COM",
    "Synthetic Rubber": "SBR:COM",
    "Soda Ash": "SODASH:COM",
    "Neodymium": "SREMNDM:COM",
    "Styrene": "STR:COM",
    "Sulfur": "SULF:COM",
    "Tellurium": "TEC:COM",
    "Urea": "UFB:COM",
    "Di-ammonium": "UFI:COM",
    "Magnesium": "MACN:COM",
    "Gallium": "GAC:COM",
    "Germanium": "GECNYBGQ:COM",
    "Manganese": "IMR:COM",
    "Indium": "IUC:COM",
    "Kraft Pulp": "KSP:COM",
}

LIVESTOCK_NAME_TO_TICKER: Final[dict[str, str]] = {
    "Feeder Cattle": "FC1:COM",
    "Live Cattle": "LC1:COM",
    "Lean Hogs": "LH1:COM",
    "Beef": "BEEF:COM",
    "Poultry": "POUL:COM",
    "Eggs US": "WEGGS:COM",
    "Eggs CH": "DCE:COM",
    "Salmon": "NOSMFZ:COM",
}

INDEX_NAME_TO_TICKER: Final[dict[str, str]] = {
    "CRB Index": "CRYTR:IND",
    "GSCI": "SPGSCITR:IND",
    "SSE Commodity Index": "SSECC:COM",
    "World Container Index": "WCI:COM",
    "Containerized Freight Index": "SPSCFI:COM",
    "EU Carbon Permits": "EECXM:IND",
    "Wind Energy Index": "GWETR:IND",
    "Nuclear Energy Index": "MVNLRTR:IND",
    "Solar Energy Index": "SOLARNTR:IND",
}

ELECTRICITY_NAME_TO_TICKER: Final[dict[str, str]] = {
    "United Kingdom": "GBRELEPRI:COM",
    "Germany": "DEUELEPRI:COM",
    "France": "FRAELEPRI:COM",
    "Italy": "ITAELEPRI:COM",
    "Spain": "ESPELEPRI:COM",
}

COMMODITY_CATEGORIES: Final[tuple[str, ...]] = (
    "Energy",
    "Metals",
    "Agricultural",
    "Industrial",
    "Livestock",
    "Index",
    "Electricity",
)

NAME_TO_TICKER_BY_CATEGORY: Final[dict[str, dict[str, str]]] = {
    "Energy": dict(ENERGY_NAME_TO_TICKER),
    "Metals": dict(METALS_NAME_TO_TICKER),
    "Agricultural": dict(AGRICULTURAL_NAME_TO_TICKER),
    "Industrial": dict(INDUSTRIAL_NAME_TO_TICKER),
    "Livestock": dict(LIVESTOCK_NAME_TO_TICKER),
    "Index": dict(INDEX_NAME_TO_TICKER),
    "Electricity": dict(ELECTRICITY_NAME_TO_TICKER),
}

TICKER_TO_NAME_BY_CATEGORY: Final[dict[str, dict[str, str]]] = {
    cat: {sym: name for name, sym in table.items()}
    for cat, table in NAME_TO_TICKER_BY_CATEGORY.items()
}

# Flattened name → ticker (all sections). Names are unique on the current page.
ALL_COMMODITY_NAME_TO_TICKER: Final[dict[str, str]] = {
    name: sym for table in NAME_TO_TICKER_BY_CATEGORY.values() for name, sym in table.items()
}

ALL_COMMODITY_TICKER_TO_NAME: Final[dict[str, str]] = {
    sym: name for name, sym in ALL_COMMODITY_NAME_TO_TICKER.items()
}

ENERGY_TICKER_TO_NAME: Final[dict[str, str]] = TICKER_TO_NAME_BY_CATEGORY["Energy"]
METALS_TICKER_TO_NAME: Final[dict[str, str]] = TICKER_TO_NAME_BY_CATEGORY["Metals"]
AGRICULTURAL_TICKER_TO_NAME: Final[dict[str, str]] = TICKER_TO_NAME_BY_CATEGORY["Agricultural"]
INDUSTRIAL_TICKER_TO_NAME: Final[dict[str, str]] = TICKER_TO_NAME_BY_CATEGORY["Industrial"]
LIVESTOCK_TICKER_TO_NAME: Final[dict[str, str]] = TICKER_TO_NAME_BY_CATEGORY["Livestock"]
INDEX_TICKER_TO_NAME: Final[dict[str, str]] = TICKER_TO_NAME_BY_CATEGORY["Index"]
ELECTRICITY_TICKER_TO_NAME: Final[dict[str, str]] = TICKER_TO_NAME_BY_CATEGORY["Electricity"]
