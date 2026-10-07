from datetime import datetime, timezone, timedelta, time
from typing import Dict, Any

# Indian Standard Time (IST) offset: UTC + 5:30
IST_OFFSET = timedelta(hours=5, minutes=30)
IST_TZ = timezone(IST_OFFSET, name="Asia/Kolkata")

# Standard recognized NSE/BSE public holidays (month, day)
NSE_HOLIDAYS_MM_DD = {
    (1, 26),   # Republic Day
    (3, 8),    # Mahashivratri (approx)
    (3, 25),   # Holi (approx)
    (3, 29),   # Good Friday (approx)
    (4, 11),   # Eid-ul-Fitr (approx)
    (4, 17),   # Ram Navami (approx)
    (5, 1),    # Maharashtra Day
    (6, 17),   # Bakri Eid (approx)
    (7, 17),   # Muharram (approx)
    (8, 15),   # Independence Day
    (10, 2),   # Mahatma Gandhi Jayanti
    (11, 1),   # Diwali Laxmi Pujan (approx)
    (11, 15),  # Gurunanak Jayanti (approx)
    (12, 25),  # Christmas
}


def get_ist_now() -> datetime:
    """Return the current datetime in Indian Standard Time (IST)."""
    return datetime.now(timezone.utc).astimezone(IST_TZ)


def format_ist_timestamp(dt: datetime) -> str:
    """Format datetime as human-readable IST string e.g. 14:32:15 IST."""
    return dt.strftime("%H:%M:%S IST")


def get_market_status(provider_is_live: bool = False, provider_name: str = "TrueData") -> Dict[str, Any]:
    """
    Calculate the accurate market status for Indian stock exchanges (NSE/BSE).
    Returns operational phase, formatted timestamp, schedule notes, and provider status.
    """
    now_ist = get_ist_now()
    weekday = now_ist.weekday()  # Monday is 0, Sunday is 6
    month_day = (now_ist.month, now_ist.day)
    current_time = now_ist.time()

    is_weekend = weekday in (5, 6)
    is_holiday = month_day in NSE_HOLIDAYS_MM_DD

    # Default market phase evaluation
    if is_weekend:
        day_name = "Saturday" if weekday == 5 else "Sunday"
        market_phase = "MARKET CLOSED"
        phase_description = f"Exchange closed for the weekend ({day_name}). Regular trading resumes Monday at 09:15 AM IST."
        is_trading_active = False
    elif is_holiday:
        market_phase = "MARKET CLOSED"
        phase_description = "Exchange closed in observance of a declared market holiday. Normal trading resumes next business day."
        is_trading_active = False
    else:
        # Weekday schedule
        pre_open_start = time(9, 0)
        pre_open_matching = time(9, 8)
        market_open = time(9, 15)
        market_close = time(15, 30)
        post_market_end = time(15, 40)

        if current_time < pre_open_start:
            market_phase = "MARKET CLOSED"
            phase_description = "Market is closed. Pre-market session commences at 09:00 AM IST."
            is_trading_active = False
        elif pre_open_start <= current_time < pre_open_matching:
            market_phase = "PRE-OPEN"
            phase_description = "Pre-market order collection session active (09:00 - 09:08 AM IST)."
            is_trading_active = False
        elif pre_open_matching <= current_time < market_open:
            market_phase = "PRE-OPEN MATCHING"
            phase_description = "Pre-market order matching and opening price discovery active (09:08 - 09:15 AM IST)."
            is_trading_active = False
        elif market_open <= current_time <= market_close:
            market_phase = "MARKET OPEN"
            phase_description = "Continuous trading session active on NSE & BSE (09:15 AM - 03:30 PM IST)."
            is_trading_active = True
        elif market_close < current_time <= post_market_end:
            market_phase = "POST-MARKET"
            phase_description = "Post-market closing price session active (03:30 - 03:40 PM IST)."
            is_trading_active = False
        else:
            market_phase = "MARKET CLOSED"
            phase_description = "Trading session closed for the day. Resumes next business day at 09:15 AM IST."
            is_trading_active = False

    # Provider health and live availability flag
    provider_status = "LIVE" if provider_is_live else "UNCONFIGURED"

    return {
        "market_status": market_phase,
        "phase_description": phase_description,
        "is_trading_active": is_trading_active,
        "server_time_ist": now_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
        "time_formatted": format_ist_timestamp(now_ist),
        "timezone": "Asia/Kolkata (IST, UTC+5:30)",
        "exchange": "NSE / BSE",
        "provider_name": provider_name,
        "provider_status": provider_status,
        "data_status": "LIVE" if provider_is_live else "DEVELOPMENT DATA",
        "notice": (
            "Connected to external provider feed."
            if provider_is_live
            else "TrueData API credentials not configured. Market running on deterministic benchmark reference data."
        ),
    }
