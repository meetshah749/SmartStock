import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.core.config import settings


@pytest.mark.asyncio
async def test_virtual_trading_lifecycle():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        email = "virtualtrader@smartstock.ai"
        password = "TradeSecurePass123!"

        # 1. Register User (gets auto ₹500.00 wallet)
        reg_res = await ac.post(
            f"{settings.API_V1_STR}/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "Virtual Trader",
                "terms_of_service": True,
                "privacy_policy": True,
                "risk_disclaimer": True,
            },
        )
        assert reg_res.status_code == 201
        token = reg_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Check Wallet Balance
        bal_res = await ac.get(f"{settings.API_V1_STR}/wallet/balance", headers=headers)
        assert bal_res.status_code == 200
        assert bal_res.json()["balance_paise"] == 50000
        assert bal_res.json()["balance_rupees"] == 500.0

        # 3. Attempt Buy Order exceeding balance -> expect 400
        overbuy_res = await ac.post(
            f"{settings.API_V1_STR}/orders/buy",
            headers=headers,
            json={"symbol": "RELIANCE", "quantity": 10},  # ~₹29,805 exceeding ₹500
        )
        assert overbuy_res.status_code == 400
        assert "Insufficient virtual wallet balance" in overbuy_res.json()["detail"]

        # 4. Execute valid Virtual Buy (e.g. 1 share of INFY @ ~₹1,945 - wait, INFY is ₹1,945, AAPL is ~$224, TATAMOTORS is ₹985 - wait, TATAMOTORS is ₹985. Let's test a stock within ₹500 or test custom balance)
        # Wait, TATAMOTORS is ₹985 which exceeds ₹500 too. Let's test AAPL (224.50 USD) or check quote execution.
        buy_res = await ac.post(
            f"{settings.API_V1_STR}/orders/buy",
            headers=headers,
            json={"symbol": "AAPL", "quantity": 1},  # $224.50 = ~₹224.50 within ₹500
        )
        assert buy_res.status_code == 201
        buy_data = buy_res.json()
        assert buy_data["symbol"] == "AAPL"
        assert buy_data["order_type"] == "BUY"
        assert buy_data["status"] == "FILLED"
        assert buy_data["is_virtual"] is True

        # 5. Check Portfolio Holdings
        hold_res = await ac.get(f"{settings.API_V1_STR}/portfolio/holdings", headers=headers)
        assert hold_res.status_code == 200
        holdings = hold_res.json()
        assert len(holdings) == 1
        assert holdings[0]["symbol"] == "AAPL"
        assert holdings[0]["quantity"] == 1

        # 6. Execute Virtual Sell
        sell_res = await ac.post(
            f"{settings.API_V1_STR}/orders/sell",
            headers=headers,
            json={"symbol": "AAPL", "quantity": 1},
        )
        assert sell_res.status_code == 201
        sell_data = sell_res.json()
        assert sell_data["order_type"] == "SELL"

        # 7. Verify Ledger entries
        ledger_res = await ac.get(f"{settings.API_V1_STR}/wallet/ledger", headers=headers)
        assert ledger_res.status_code == 200
        ledger = ledger_res.json()
        assert len(ledger) == 3  # DEMO_CREDIT, VIRTUAL_BUY, VIRTUAL_SELL
