"""Auth resolvers — all unauthenticated (no guard)."""
from __future__ import annotations
import uuid
import strawberry
from mock_server.types import (
    OtpRequestInput, OtpRequestResponse, OtpResponsePayloadDto,
    VerifyOtpInput, LoginResponse, LoginPayloadDto, AuthTokensDto,
    LoginInput, RegisterInput, AuthnUserResponse, ForgotPasswordInput,
    RefreshTokensInput, EmptyResponse, ResponseMetaDto, authn_user_from_dict,
)
from mock_server.store import store
from mock_server.seed import MOCK_ACCESS_TOKEN, MOCK_REFRESH_TOKEN
from mock_server.utils import utc_now, maybe_delay


def _mock_tokens() -> AuthTokensDto:
    return AuthTokensDto(
        access_token=MOCK_ACCESS_TOKEN,
        refresh_token=MOCK_REFRESH_TOKEN,
        token_type="Bearer",
        expires_in=3600,
        scope="read write",
    )


async def request_otp(input: OtpRequestInput) -> OtpRequestResponse:
    await maybe_delay()
    return OtpRequestResponse(
        success=True,
        status=200,
        message="OTP sent successfully.",
        meta=ResponseMetaDto(timestamp=utc_now()),
        payload=OtpResponsePayloadDto(
            otp_sent=True,
            expires_in_seconds=300,
            delivery_method="sms" if input.input.identifier_type.value == "phone" else "email",
        ),
    )


async def verify_otp(input: VerifyOtpInput) -> LoginResponse:
    await maybe_delay()
    user = store.users[0]  # Always Jane for mock
    return LoginResponse(
        success=True,
        status=200,
        message="OTP verified successfully.",
        meta=ResponseMetaDto(timestamp=utc_now()),
        payload=LoginPayloadDto(
            user=authn_user_from_dict(user),
            tokens=_mock_tokens(),
        ),
    )


async def login(input: LoginInput) -> LoginResponse:
    await maybe_delay()
    
    # ─── MOCK ERROR SCENARIOS FOR FRONTEND TESTING ───
    login_email = input.input.login.lower()
    login_password = input.input.password.lower()
    
    if login_email == "wrong@example.com":
        raise Exception("Invalid credentials. User not found.")
    
    if login_password in ("wrong", "error", "invalid"):
        raise Exception("Invalid credentials. Incorrect password.")
    # ─────────────────────────────────────────────────

    user = store.users[0]  # Always Jane for mock
    return LoginResponse(
        success=True,
        status=200,
        message="Login successful.",
        meta=ResponseMetaDto(timestamp=utc_now()),
        payload=LoginPayloadDto(
            user=authn_user_from_dict(user),
            tokens=_mock_tokens(),
        ),
    )


async def register(input: RegisterInput) -> AuthnUserResponse:
    await maybe_delay()
    payload = input.input
    new_user = {
        "id": str(uuid.uuid4()),
        "email": payload.email,
        "first_name": payload.first_name,
        "last_name": payload.last_name,
        "phone_number": payload.phone_number or "",
        "is_active": True,
        "email_verified": False,
        "phone_verified": False,
        "market_id": payload.market_id,
        "date_joined": utc_now(),
        "created_at": utc_now(),
    }
    store.add_user(new_user)
    return AuthnUserResponse(
        success=True,
        status=201,
        message="Registration successful.",
        meta=ResponseMetaDto(timestamp=utc_now()),
        payload=authn_user_from_dict(new_user),
    )


async def forgot_password(input: ForgotPasswordInput) -> EmptyResponse:
    await maybe_delay()
    return EmptyResponse(
        success=True,
        status=200,
        message="If an account with that identifier exists, a reset link has been sent.",
        meta=ResponseMetaDto(timestamp=utc_now()),
    )


async def refresh_tokens(input: RefreshTokensInput) -> LoginResponse:
    await maybe_delay()
    user = store.users[0]  # Always Jane for mock
    return LoginResponse(
        success=True,
        status=200,
        message="Tokens refreshed successfully.",
        meta=ResponseMetaDto(timestamp=utc_now()),
        payload=LoginPayloadDto(
            user=authn_user_from_dict(user),
            tokens=_mock_tokens(),
        ),
    )
