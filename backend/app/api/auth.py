"""Authentication endpoints: register and login."""

from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import DbSessionDep
from app.core.logging import get_logger
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new CRM user",
)
async def register(payload: RegisterRequest, session: DbSessionDep) -> TokenResponse:
    """Create a new user account and return an access token."""
    repo = UserRepository(session)

    existing = await repo.get_by_email(payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=True,
    )
    user = await repo.create(user)
    await session.commit()

    logger.info("New user registered: %s (%s)", user.email, user.role)

    token = create_access_token(user_id=str(user.id), role=user.role.value)
    return TokenResponse(
        access_token=token,
        user_id=str(user.id),
        role=user.role.value,
        full_name=user.full_name,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive a JWT access token",
)
async def login(payload: LoginRequest, session: DbSessionDep) -> TokenResponse:
    """Verify credentials and return a signed JWT access token."""
    repo = UserRepository(session)

    user = await repo.get_by_email(payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Contact an administrator.",
        )

    logger.info("User logged in: %s", user.email)

    token = create_access_token(user_id=str(user.id), role=user.role.value)
    return TokenResponse(
        access_token=token,
        user_id=str(user.id),
        role=user.role.value,
        full_name=user.full_name,
    )
