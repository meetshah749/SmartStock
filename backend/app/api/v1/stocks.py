import json
import asyncio
from typing import Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, status, Depends, WebSocket, WebSocketDisconnect

from app.services.market_data import get_market_provider, BaseMarketDataProvider
from app.services.indicators import compute_indicators_series
from app.services.symbol_mapper import normalize_symbol
from app.services.stock_universe import list_indian_equities

router = APIRouter(prefix="/stocks", tags=["Market Data & Stocks"])


@router.get("/status", response_model=dict)
async def get_market_operational_status(
    provider: BaseMarketDataProvider = Depends(get_market_provider),
) -> Any:
    """Return exchange operating status (OPEN, CLOSED, PRE-OPEN) and data provider health."""
    return await provider.get_market_status()


@router.get("/search", response_model=List[dict])
async def search_stocks(
    q: str = Query(..., min_length=1, description="Search query by symbol or company name"),
    provider: BaseMarketDataProvider = Depends(get_market_provider),
) -> Any:
    results = await provider.search_stocks(q)
    return results


@router.get("/indices", response_model=List[dict])
async def get_market_indices(
    provider: BaseMarketDataProvider = Depends(get_market_provider),
) -> Any:
    indices = await provider.get_market_indices()
    return indices


@router.get("/universe", response_model=List[dict])
async def list_stock_universe(
    q: Optional[str] = Query(None, min_length=1, description="Filter by symbol, company, or sector"),
    exchange: Optional[str] = Query(None, description="Filter for NSE or BSE listings"),
    limit: int = Query(250, ge=1, le=500),
) -> Any:
    """Return the curated Indian equity directory without making hundreds of quote requests."""
    entries = list_indian_equities()
    if q:
        query = q.casefold().strip()
        entries = [
            item for item in entries
            if query in item["symbol"].casefold()
            or query in item["company_name"].casefold()
            or query in item["sector"].casefold()
            or query in item["industry"].casefold()
        ]
    if exchange:
        exchange_normalized = exchange.strip().upper()
        entries = [item for item in entries if exchange_normalized in item["listing_exchanges"]]
    return entries[:limit]


@router.get("", response_model=List[dict])
async def list_stocks(
    provider: BaseMarketDataProvider = Depends(get_market_provider),
) -> Any:
    # Standard catalog of top Indian Equities
    catalog = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "ITC", "TATAMOTORS"]
    results = []
    for s in catalog:
        quote = await provider.get_stock_quote(s)
        if quote:
            results.append(quote)
    return results


@router.get("/{symbol}", response_model=dict)
async def get_stock_details(
    symbol: str,
    provider: BaseMarketDataProvider = Depends(get_market_provider),
) -> Any:
    info = await provider.get_company_info(symbol)
    quote = await provider.get_stock_quote(symbol)
    if not info or not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock with symbol '{symbol}' not found",
        )
    return {**info, "quote": quote}


@router.get("/{symbol}/quote", response_model=dict)
async def get_stock_quote(
    symbol: str,
    provider: BaseMarketDataProvider = Depends(get_market_provider),
) -> Any:
    quote = await provider.get_stock_quote(symbol)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock with symbol '{symbol}' not found",
        )
    return quote


@router.get("/{symbol}/prices", response_model=List[dict])
async def get_stock_historical_prices(
    symbol: str,
    timeframe: str = Query("1D", description="Timeframe: 1D, 1W, 1M, 3M, 6M, 1Y, 5Y"),
    provider: BaseMarketDataProvider = Depends(get_market_provider),
) -> Any:
    history = await provider.get_historical_prices(symbol, timeframe=timeframe)
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Historical price data for '{symbol}' not available",
        )
    return history


@router.get("/{symbol}/indicators", response_model=dict)
async def get_stock_indicators(
    symbol: str,
    timeframe: str = Query("1D", description="Timeframe for indicator computation"),
    provider: BaseMarketDataProvider = Depends(get_market_provider),
) -> Any:
    history = await provider.get_historical_prices(symbol, timeframe=timeframe)
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Historical data for '{symbol}' not available",
        )
    indicators = compute_indicators_series(history)
    return {
        "symbol": normalize_symbol(symbol),
        "timeframe": timeframe,
        "indicators": indicators,
    }


@router.websocket("/ws")
async def market_data_websocket(websocket: WebSocket):
    """
    Real-time market data WebSocket gateway.
    Streams normalized ticks from external provider to connected frontend clients,
    or broadcasts provider status and heartbeats when live stream is unavailable.
    """
    await websocket.accept()
    provider = get_market_provider()
    subscribed_symbols: set = set()

    # Initial connection status notification
    init_status = {
        "type": "status",
        "connection": "connected",
        "provider_name": provider.provider_name(),
        "provider_status": provider.provider_status(),
        "is_live": provider.is_live_provider(),
        "data_status": "LIVE" if provider.is_live_provider() else "DEVELOPMENT DATA",
        "message": (
            "Connected to live market data feed."
            if provider.is_live_provider()
            else "TrueData credentials not configured. Live streaming paused; displaying benchmark reference data."
        ),
    }
    await websocket.send_text(json.dumps(init_status))

    async def heartbeat_sender():
        try:
            while True:
                await asyncio.sleep(15)
                # Send periodic heartbeat / status
                m_status = await provider.get_market_status()
                hb = {
                    "type": "heartbeat",
                    "market_status": m_status["market_status"],
                    "time_formatted": m_status["time_formatted"],
                    "data_status": m_status["data_status"],
                    "provider_status": provider.provider_status(),
                }
                await websocket.send_text(json.dumps(hb))
        except (asyncio.CancelledError, WebSocketDisconnect):
            pass
        except Exception:
            pass

    hb_task = asyncio.create_task(heartbeat_sender())

    try:
        while True:
            text = await websocket.receive_text()
            try:
                msg = json.loads(text)
                msg_type = msg.get("type")
                if msg_type == "subscribe":
                    symbols = [normalize_symbol(s) for s in msg.get("symbols", [])]
                    subscribed_symbols.update(symbols)
                    await provider.subscribe_realtime(symbols)
                    # Respond with latest quote for each subscribed symbol
                    for s in symbols:
                        q = await provider.get_stock_quote(s)
                        if q:
                            await websocket.send_text(json.dumps({"type": "quote", "data": q}))
                elif msg_type == "unsubscribe":
                    symbols = [normalize_symbol(s) for s in msg.get("symbols", [])]
                    for s in symbols:
                        subscribed_symbols.discard(s)
                    await provider.unsubscribe_realtime(symbols)
                elif msg_type == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        pass
    finally:
        hb_task.cancel()
        if subscribed_symbols:
            await provider.unsubscribe_realtime(list(subscribed_symbols))
