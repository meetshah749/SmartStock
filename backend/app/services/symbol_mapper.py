"""
Canonical Symbol Mapping for Indian Stock Exchanges (NSE/BSE).
Normalizes tickers, handles user search variations, and maps to external provider instruments.
"""

from typing import Dict, Any, Optional, List
from app.services.stock_universe import INDIAN_EQUITY_ALIASES, INDIAN_EQUITY_UNIVERSE

# Standardized Instrument Catalog for SmartStock AI
INSTRUMENT_CATALOG: Dict[str, Dict[str, Any]] = {
    "RELIANCE": {
        "symbol": "RELIANCE",
        "company_name": "Reliance Industries Limited",
        "exchange": "NSE",
        "sector": "Energy & Conglomerate",
        "industry": "Oil & Gas, Refining, Retail, Telecom",
        "isin": "INE002A01018",
        "truedata_symbol": "RELIANCE-EQ",
        "currency": "INR",
        "base_price": 2980.50,
        "prev_close": 2940.00,
        "high_52w": 3217.90,
        "low_52w": 2220.30,
        "day_high": 2998.00,
        "day_low": 2935.00,
        "volume": 5420110,
        "description": "Reliance Industries Limited is an Indian multinational conglomerate headquartered in Mumbai. Businesses include energy, petrochemicals, retail, telecommunications (Jio), and textiles.",
    },
    "TCS": {
        "symbol": "TCS",
        "company_name": "Tata Consultancy Services Limited",
        "exchange": "NSE",
        "sector": "Information Technology",
        "industry": "IT Services & Consulting",
        "isin": "INE467B01029",
        "truedata_symbol": "TCS-EQ",
        "currency": "INR",
        "base_price": 4210.75,
        "prev_close": 4185.20,
        "high_52w": 4592.25,
        "low_52w": 3313.00,
        "day_high": 4245.00,
        "day_low": 4170.00,
        "volume": 2130440,
        "description": "Tata Consultancy Services is an Indian multinational information technology consulting company. Part of the Tata Group, operating in over 46 countries worldwide.",
    },
    "INFY": {
        "symbol": "INFY",
        "company_name": "Infosys Limited",
        "exchange": "NSE",
        "sector": "Information Technology",
        "industry": "IT Software & Consulting",
        "isin": "INE009A01021",
        "truedata_symbol": "INFY-EQ",
        "currency": "INR",
        "base_price": 1945.30,
        "prev_close": 1920.00,
        "high_52w": 1991.45,
        "low_52w": 1358.35,
        "day_high": 1962.00,
        "day_low": 1915.00,
        "volume": 4890200,
        "description": "Infosys Limited is a global leader in next-generation digital services and consulting, enabling clients across 56 countries to navigate their digital transformation.",
    },
    "HDFCBANK": {
        "symbol": "HDFCBANK",
        "company_name": "HDFC Bank Limited",
        "exchange": "NSE",
        "sector": "Financial Services",
        "industry": "Private Sector Banking",
        "isin": "INE040A01034",
        "truedata_symbol": "HDFCBANK-EQ",
        "currency": "INR",
        "base_price": 1660.10,
        "prev_close": 1672.40,
        "high_52w": 1794.00,
        "low_52w": 1363.55,
        "day_high": 1675.00,
        "day_low": 1652.50,
        "volume": 11240800,
        "description": "HDFC Bank Limited is an Indian banking and financial services company headquartered in Mumbai. It is India's largest private sector bank by assets and market capitalization.",
    },
    "ICICIBANK": {
        "symbol": "ICICIBANK",
        "company_name": "ICICI Bank Limited",
        "exchange": "NSE",
        "sector": "Financial Services",
        "industry": "Private Sector Banking",
        "isin": "INE090A01021",
        "truedata_symbol": "ICICIBANK-EQ",
        "currency": "INR",
        "base_price": 1235.80,
        "prev_close": 1228.00,
        "high_52w": 1300.90,
        "low_52w": 918.00,
        "day_high": 1242.00,
        "day_low": 1225.00,
        "volume": 8760000,
        "description": "ICICI Bank Limited is an Indian multinational banking and financial services company offering a wide range of banking products and financial services.",
    },
    "SBIN": {
        "symbol": "SBIN",
        "company_name": "State Bank of India",
        "exchange": "NSE",
        "sector": "Financial Services",
        "industry": "Public Sector Banking",
        "isin": "INE062A01020",
        "truedata_symbol": "SBIN-EQ",
        "currency": "INR",
        "base_price": 792.40,
        "prev_close": 786.10,
        "high_52w": 912.00,
        "low_52w": 555.25,
        "day_high": 798.50,
        "day_low": 784.00,
        "volume": 14200300,
        "description": "State Bank of India is an Indian multinational public sector bank and financial services statutory body headquartered in Mumbai. It is the 48th largest bank in the world by total assets.",
    },
    "ITC": {
        "symbol": "ITC",
        "company_name": "ITC Limited",
        "exchange": "NSE",
        "sector": "Consumer Goods & FMCG",
        "industry": "FMCG, Hotels, Paperboards, Agri-Business",
        "isin": "INE154A01025",
        "truedata_symbol": "ITC-EQ",
        "currency": "INR",
        "base_price": 502.15,
        "prev_close": 498.80,
        "high_52w": 528.55,
        "low_52w": 399.30,
        "day_high": 505.00,
        "day_low": 497.00,
        "volume": 9840100,
        "description": "ITC Limited is an Indian conglomerate company headquartered in Kolkata. Its businesses include FMCG, Hotels, Paperboards & Packaging, Agri Business, and Information Technology.",
    },
    "TATAMOTORS": {
        "symbol": "TATAMOTORS",
        "company_name": "Tata Motors Limited",
        "exchange": "NSE",
        "sector": "Automotive",
        "industry": "Automobile Manufacturer",
        "isin": "INE155A01022",
        "truedata_symbol": "TATAMOTORS-EQ",
        "currency": "INR",
        "base_price": 985.60,
        "prev_close": 962.00,
        "high_52w": 1179.05,
        "low_52w": 621.75,
        "day_high": 994.00,
        "day_low": 960.00,
        "volume": 7650400,
        "description": "Tata Motors Limited is an Indian multinational automotive manufacturing company headquartered in Mumbai, part of the Tata Group, producing passenger cars, trucks, and luxury vehicles (JLR).",
    },
}

# Major Indices Mapping
INDICES_CATALOG: Dict[str, Dict[str, Any]] = {
    "NIFTY50": {
        "symbol": "NIFTY50",
        "canonical_name": "NIFTY 50",
        "exchange": "NSE",
        "truedata_symbol": "NIFTY-I",
        "price": 25380.40,
        "prev_close": 25237.80,
        "change": 142.60,
        "change_percent": 0.56,
        "currency": "INR",
    },
    "SENSEX": {
        "symbol": "SENSEX",
        "canonical_name": "BSE SENSEX",
        "exchange": "BSE",
        "truedata_symbol": "SENSEX",
        "price": 82950.15,
        "prev_close": 82529.85,
        "change": 420.30,
        "change_percent": 0.51,
        "currency": "INR",
    },
    "BANKNIFTY": {
        "symbol": "BANKNIFTY",
        "canonical_name": "NIFTY BANK",
        "exchange": "NSE",
        "truedata_symbol": "BANKNIFTY-I",
        "price": 52140.80,
        "prev_close": 52226.00,
        "change": -85.20,
        "change_percent": -0.16,
        "currency": "INR",
    },
}

# Aliases for fuzzy resolution
SYMBOL_ALIASES: Dict[str, str] = {
    "RELIANCE": "RELIANCE",
    "RIL": "RELIANCE",
    "TCS": "TCS",
    "TATA CONSULTANCY": "TCS",
    "INFY": "INFY",
    "INFOSYS": "INFY",
    "HDFCBANK": "HDFCBANK",
    "HDFC": "HDFCBANK",
    "HDFC BANK": "HDFCBANK",
    "ICICIBANK": "ICICIBANK",
    "ICICI": "ICICIBANK",
    "SBIN": "SBIN",
    "SBI": "SBIN",
    "STATE BANK": "SBIN",
    "ITC": "ITC",
    "TATAMOTORS": "TATAMOTORS",
    "TATA MOTORS": "TATAMOTORS",
    "NIFTY": "NIFTY50",
    "NIFTY 50": "NIFTY50",
    "NIFTY50": "NIFTY50",
    "SENSEX": "SENSEX",
    "BSE SENSEX": "SENSEX",
    "BANKNIFTY": "BANKNIFTY",
    "NIFTY BANK": "BANKNIFTY",
}
SYMBOL_ALIASES.update(INDIAN_EQUITY_ALIASES)
SYMBOL_ALIASES.update({
    details["company_name"].upper(): symbol
    for symbol, details in INDIAN_EQUITY_UNIVERSE.items()
})


def normalize_symbol(query: str) -> str:
    """Normalize input ticker or query to canonical symbol."""
    raw = query.strip().upper()
    # Preserve Yahoo-style exchange-qualified tickers (e.g. RELIANCE.NS, TATAMOTORS.BO).
    if raw.endswith((".NS", ".BO")):
        return raw
    if raw in INDIAN_EQUITY_UNIVERSE:
        return raw
    cleaned = raw.replace(".", "").replace("-", " ")
    if cleaned in SYMBOL_ALIASES:
        return SYMBOL_ALIASES[cleaned]
    # Check if direct match
    if cleaned in INSTRUMENT_CATALOG:
        return cleaned
    # Collapse spaces
    nospace = cleaned.replace(" ", "")
    if nospace in SYMBOL_ALIASES:
        return SYMBOL_ALIASES[nospace]
    if nospace in INSTRUMENT_CATALOG:
        return nospace
    if nospace in INDIAN_EQUITY_UNIVERSE:
        return nospace
    return cleaned


def get_truedata_symbol(canonical_symbol: str) -> str:
    """Map canonical symbol to TrueData instrument symbol."""
    if canonical_symbol in INSTRUMENT_CATALOG:
        return INSTRUMENT_CATALOG[canonical_symbol].get("truedata_symbol", f"{canonical_symbol}-EQ")
    if canonical_symbol in INDIAN_EQUITY_UNIVERSE:
        return f"{canonical_symbol}-EQ"
    if canonical_symbol in INDICES_CATALOG:
        return INDICES_CATALOG[canonical_symbol].get("truedata_symbol", canonical_symbol)
    return canonical_symbol
