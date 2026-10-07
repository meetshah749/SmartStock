import random
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.database.session import get_async_db
from app.models.user import User, Wallet, WalletLedger
from app.models.auth import (
    ConsentRecord,
    EmailVerification,
    PasswordResetToken,
    RefreshToken,
    UserProfile,
)
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    TokenResponse,
    UserOut,
    RefreshTokenRequest,
    VerifyEmailRequest,
    ResendVerificationRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserRegister,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    if not (user_in.terms_of_service and user_in.privacy_policy and user_in.risk_disclaimer):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must accept the Terms of Service, Privacy Policy, and Risk Disclaimer to register.",
        )

    existing_user = await db.execute(select(User).where(User.email == user_in.email))
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address already exists.",
        )

    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    await db.flush()

    default_balance = settings.DEFAULT_VIRTUAL_BALANCE_PAISE
    wallet = Wallet(
        user_id=user.id,
        balance_paise=default_balance,
        currency="INR",
    )
    db.add(wallet)
    await db.flush()

    ledger_entry = WalletLedger(
        wallet_id=wallet.id,
        amount_paise=default_balance,
        balance_before_paise=0,
        balance_after_paise=default_balance,
        transaction_type="DEMO_CREDIT",
        reference_id=f"INITIAL_DEMO_CREDIT_{user.id[:8]}",
    )
    db.add(ledger_entry)

    profile = UserProfile(
        user_id=user.id,
        experience_level="beginner",
        preferred_market="NSE",
    )
    db.add(profile)

    client_ip = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "Unknown")
    consent = ConsentRecord(
        user_id=user.id,
        terms_of_service=user_in.terms_of_service,
        privacy_policy=user_in.privacy_policy,
        risk_disclaimer=user_in.risk_disclaimer,
        ip_address=client_ip,
        user_agent=user_agent,
    )
    db.add(consent)

    verification_code = f"{random.randint(100000, 999999)}"
    verification = EmailVerification(
        user_id=user.id,
        code=verification_code,
        token=hashlib.sha256(f"{user.id}:{verification_code}".encode()).hexdigest(),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(verification)

    access_token = create_access_token(subject=user.id)
    raw_refresh = create_refresh_token(subject=user.id)
    refresh_hash = hashlib.sha256(raw_refresh.encode()).hexdigest()

    refresh_db = RefreshToken(
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(refresh_db)

    await db.commit()
    await db.refresh(user)

    logger.info(f"User registered successfully: {user.email} (Verification Code: {verification_code})")

    user_out = UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        wallet_balance_paise=wallet.balance_paise,
        wallet_balance_rupees=wallet.balance_paise / 100.0,
    )

    smtp_active = bool(settings.SMTP_HOST and settings.SMTP_USER)
    email_status = "sent" if smtp_active else "not_configured"
    dev_msg = (
        "Verification email dispatched to your inbox."
        if smtp_active
        else "Email service not configured — development verification mode."
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        token_type="bearer",
        user=user_out,
        email_status=email_status,
        dev_verification_code=verification_code if not smtp_active else None,
        dev_verification_token=verification.token if not smtp_active else None,
        message=dev_msg,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    stmt = select(User).where(User.email == credentials.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is inactive",
        )

    wallet_stmt = select(Wallet).where(Wallet.user_id == user.id)
    wallet_res = await db.execute(wallet_stmt)
    wallet = wallet_res.scalar_one_or_none()
    balance_paise = wallet.balance_paise if wallet else 50000

    access_token = create_access_token(subject=user.id)
    raw_refresh = create_refresh_token(subject=user.id)
    refresh_hash = hashlib.sha256(raw_refresh.encode()).hexdigest()

    refresh_db = RefreshToken(
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(refresh_db)
    await db.commit()

    logger.info(f"User logged in successfully: {user.email}")

    user_out = UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
        is_admin=user.is_admin,
        created_at=user.created_at,
        wallet_balance_paise=balance_paise,
        wallet_balance_rupees=balance_paise / 100.0,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        token_type="bearer",
        user=user_out,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    req: RefreshTokenRequest,
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    payload = decode_token(req.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user_id = payload.get("sub")
    token_hash = hashlib.sha256(req.refresh_token.encode()).hexdigest()

    stmt = select(RefreshToken).where(
        RefreshToken.token_hash == token_hash,
        RefreshToken.is_revoked == False,
    )
    result = await db.execute(stmt)
    db_token = result.scalar_one_or_none()

    if not db_token or ensure_utc(db_token.expires_at) < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired or revoked")

    db_token.is_revoked = True

    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    new_access = create_access_token(subject=user.id)
    new_raw_refresh = create_refresh_token(subject=user.id)
    new_hash = hashlib.sha256(new_raw_refresh.encode()).hexdigest()

    new_token_db = RefreshToken(
        user_id=user.id,
        token_hash=new_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(new_token_db)
    await db.commit()

    wallet_res = await db.execute(select(Wallet).where(Wallet.user_id == user.id))
    wallet = wallet_res.scalar_one_or_none()
    balance = wallet.balance_paise if wallet else 50000

    user_out = UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
        is_admin=user.is_admin,
        created_at=user.created_at,
        wallet_balance_paise=balance,
        wallet_balance_rupees=balance / 100.0,
    )

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_raw_refresh,
        token_type="bearer",
        user=user_out,
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    req: RefreshTokenRequest,
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    token_hash = hashlib.sha256(req.refresh_token.encode()).hexdigest()
    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    result = await db.execute(stmt)
    db_token = result.scalar_one_or_none()
    if db_token:
        db_token.is_revoked = True
        await db.commit()
    return {"message": "Successfully logged out"}


@router.post("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(
    req: VerifyEmailRequest,
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    stmt = select(User).where(User.email == req.email)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.is_verified:
        return {"message": "Email is already verified.", "is_verified": True}

    if req.code:
        verif_cond = (EmailVerification.code == req.code)
    elif req.token:
        verif_cond = (EmailVerification.token == req.token)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification code or token required")

    verif_stmt = select(EmailVerification).where(
        EmailVerification.user_id == user.id,
        verif_cond,
        EmailVerification.is_used == False,
    )
    verif_res = await db.execute(verif_stmt)
    verif = verif_res.scalar_one_or_none()

    if not verif or ensure_utc(verif.expires_at) < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification code")

    verif.is_used = True
    user.is_verified = True
    await db.commit()

    return {"message": "Email address verified successfully", "is_verified": True}


@router.post("/resend-verification", status_code=status.HTTP_200_OK)
async def resend_verification(
    req: ResendVerificationRequest,
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    stmt = select(User).where(User.email == req.email)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.is_verified:
        return {"message": "Email is already verified.", "is_verified": True}

    verification_code = f"{random.randint(100000, 999999)}"
    token = hashlib.sha256(f"{user.id}:{verification_code}".encode()).hexdigest()
    verification = EmailVerification(
        user_id=user.id,
        code=verification_code,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(verification)
    await db.commit()

    smtp_active = bool(settings.SMTP_HOST and settings.SMTP_USER)
    return {
        "message": (
            "Verification email dispatched to your inbox."
            if smtp_active
            else "Email service not configured — development verification mode."
        ),
        "email_status": "sent" if smtp_active else "not_configured",
        "dev_verification_code": verification_code if not smtp_active else None,
        "dev_verification_token": token if not smtp_active else None,
    }



@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    req: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    stmt = select(User).where(User.email == req.email)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        return {"message": "If the email is registered, a password reset link has been issued."}

    reset_code = f"{random.randint(100000, 999999)}"
    reset_token = hashlib.sha256(f"{user.id}:{reset_code}".encode()).hexdigest()

    reset_entry = PasswordResetToken(
        user_id=user.id,
        token=reset_token,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.add(reset_entry)
    await db.commit()

    logger.info(f"Password reset token generated for {user.email}: Token={reset_token}")

    return {
        "message": "If the email is registered, a password reset link has been issued.",
        "dev_reset_token": reset_token if settings.DEBUG else None,
    }


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    req: ResetPasswordRequest,
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    stmt = select(PasswordResetToken).where(
        PasswordResetToken.token == req.token,
        PasswordResetToken.is_used == False,
    )
    res = await db.execute(stmt)
    reset_record = res.scalar_one_or_none()

    if not reset_record or ensure_utc(reset_record.expires_at) < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    user = await db.get(User, reset_record.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.hashed_password = get_password_hash(req.new_password)
    reset_record.is_used = True
    await db.commit()

    return {"message": "Password reset successfully. You may now log in with your new password."}
