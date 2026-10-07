import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.core.config import settings


@pytest.mark.asyncio
async def test_register_login_flow():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        test_email = "trader@smartstock.ai"
        test_pass = "SecurePass123!"

        # 1. Register new user
        reg_response = await ac.post(
            f"{settings.API_V1_STR}/auth/register",
            json={
                "email": test_email,
                "password": test_pass,
                "full_name": "Demo Trader",
                "terms_of_service": True,
                "privacy_policy": True,
                "risk_disclaimer": True,
            },
        )
        assert reg_response.status_code == 201
        reg_data = reg_response.json()
        assert "access_token" in reg_data
        assert "refresh_token" in reg_data
        assert reg_data["user"]["email"] == test_email
        assert reg_data["user"]["wallet_balance_paise"] == 50000  # ₹500.00
        assert reg_data["user"]["wallet_balance_rupees"] == 500.0

        access_token = reg_data["access_token"]
        refresh_token = reg_data["refresh_token"]

        # 2. Login user
        login_res = await ac.post(
            f"{settings.API_V1_STR}/auth/login",
            json={
                "email": test_email,
                "password": test_pass,
            },
        )
        assert login_res.status_code == 200
        login_data = login_res.json()
        assert "access_token" in login_data

        # 3. Access Protected /users/me endpoint
        me_res = await ac.get(
            f"{settings.API_V1_STR}/users/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert me_res.status_code == 200
        user_me = me_res.json()
        assert user_me["email"] == test_email

        # 4. Refresh token rotation
        refresh_res = await ac.post(
            f"{settings.API_V1_STR}/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_res.status_code == 200
        refreshed_data = refresh_res.json()
        assert "access_token" in refreshed_data
        assert refreshed_data["refresh_token"] != refresh_token


@pytest.mark.asyncio
async def test_register_without_consent_fails():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        res = await ac.post(
            f"{settings.API_V1_STR}/auth/register",
            json={
                "email": "noconsent@smartstock.ai",
                "password": "Password123!",
                "full_name": "No Consent",
                "terms_of_service": False,
                "privacy_policy": True,
                "risk_disclaimer": True,
            },
        )
        assert res.status_code == 400
        assert "accept the Terms of Service" in res.json()["detail"]
