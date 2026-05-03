from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, Any

from app.database import get_db
from app.schemas.auth import UserRegister, UserLogin, UserResponse, PasswordResetRequest, PasswordReset
from app.services.auth_manager import AuthManager
from app.services.auth_service import AuthService
from app.services.oauth_service import OAuthService
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


def create_token_response(
    response: Response,
    access_token: str,
    refresh_token: str
) -> Response:
    """
    Установка токенов в cookies с безопасными флагами.
    """
    # Устанавливаем Access Token cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,  # Защита от XSS - JavaScript не видит куку
        secure=False, 
        samesite="lax",  # Защита от CSRF
        path="/",  # Кука доступна для всех путей
        max_age=settings.JWT_ACCESS_EXPIRATION * 60  # Время жизни в секундах
    )
    
    # Устанавливаем Refresh Token cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,  # Защита от XSS
        secure=False,
        samesite="lax",  # Защита от CSRF
        path="/",
        max_age=settings.JWT_REFRESH_EXPIRATION * 60  # 7 дней в секундах
    )
    
    return response


def clear_token_cookies(response: Response) -> Response:
    """Очистка cookies с токенами (при выходе)"""
    response.delete_cookie(
        key="access_token",
        path="/",
        httponly=True,
        secure=False,
        samesite="lax"
    )
    response.delete_cookie(
        key="refresh_token",
        path="/",
        httponly=True,
        secure=False,
        samesite="lax"
    )
    return response


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового пользователя",
    description="Создает нового пользователя с хешированным паролем. Автоматически выполняет вход и устанавливает JWT токены в HttpOnly cookies.",
    responses={
        201: {
            "description": "Пользователь успешно зарегистрирован",
            "content": {
                "application/json": {
                    "example": {
                        "message": "User registered successfully",
                        "user": {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "email": "user@example.com",
                            "created_at": "2024-01-15T10:30:00",
                            "updated_at": "2024-01-15T10:30:00"
                        }
                    }
                }
            }
        },
        400: {
            "description": "Ошибка валидации данных",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid request data",
                        "errors": []
                    }
                }
            }
        },
        409: {
            "description": "Пользователь с таким email уже существует",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User with this email already exists"
                    }
                }
            }
        }
    }
)
async def register(
    register_data: UserRegister,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Регистрация нового пользователя.
    Создает пользователя с хешированным паролем.
    """
    try:
        user, access_token, refresh_token = AuthManager.register_and_login(
            db, register_data
        )
        
        # Устанавливаем токены в cookies
        create_token_response(response, access_token, refresh_token)
        
        return {
            "message": "User registered successfully",
            "user": UserResponse.model_validate(user)
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.post(
    "/login",
    summary="Вход пользователя (логин)",
    description="Аутентификация пользователя по email и паролю. При успешном входе устанавливает JWT токены в HttpOnly cookies.",
    responses={
        200: {
            "description": "Успешный вход",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Login successful",
                        "user": {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "email": "user@example.com",
                            "created_at": "2024-01-15T10:30:00",
                            "updated_at": "2024-01-15T10:30:00"
                        }
                    }
                }
            }
        },
        400: {
            "description": "Ошибка валидации данных",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid request data"}
                }
            }
        },
        401: {
            "description": "Неверный email или пароль",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid email or password"}
                }
            }
        }
    }
)
async def login(
    login_data: UserLogin,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Вход пользователя (логин).
    """
    try:
        user, access_token, refresh_token = AuthManager.login_user(
            db, login_data
        )
        
        # Устанавливаем токены в cookies
        create_token_response(response, access_token, refresh_token)
        
        return {
            "message": "Login successful",
            "user": UserResponse.model_validate(user)
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Cookie"},
        )


@router.post(
    "/refresh",
    summary="Обновление токенов",
    description="Использует Refresh Token из cookies для получения новой пары токенов. Автоматически обновляет cookies.",
    responses={
        200: {
            "description": "Токены успешно обновлены",
            "content": {
                "application/json": {
                    "example": {"message": "Tokens refreshed successfully"}
                }
            }
        },
        401: {
            "description": "Refresh токен не найден или недействителен",
            "content": {
                "application/json": {
                    "example": {"detail": "Refresh token not found"}
                }
            }
        }
    }
)
async def refresh_tokens(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Обновление пары токенов.
    Использует Refresh Token из cookies для получения новой пары токенов.
    """
    # Извлекаем refresh токен из cookies
    refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
            headers={"WWW-Authenticate": "Cookie"},
        )
    
    try:
        new_access_token, new_refresh_token = AuthManager.refresh_tokens(
            db, refresh_token
        )
        
        # Устанавливаем новые токены в cookies
        create_token_response(response, new_access_token, new_refresh_token)
        
        return {"message": "Tokens refreshed successfully"}
    except ValueError as e:
        # При ошибке очищаем cookies
        clear_token_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Cookie"},
        )


@router.get(
    "/whoami",
    response_model=UserResponse,
    summary="Проверка авторизации",
    description="Возвращает данные текущего аутентифицированного пользователя. Требует valid JWT token в cookies.",
    responses={
        200: {
            "description": "Данные текущего пользователя",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "email": "user@example.com",
                        "created_at": "2024-01-15T10:30:00",
                        "updated_at": "2024-01-15T10:30:00"
                    }
                }
            }
        },
        401: {
            "description": "Пользователь не аутентифицирован",
            "content": {
                "application/json": {
                    "example": {"detail": "Could not validate credentials"}
                }
            }
        }
    }
)
async def whoami(
    current_user: UserResponse = Depends(AuthService.get_current_user)
):
    """
    Проверка статуса авторизации и получение данных пользователя.
    """
    return current_user


@router.post(
    "/logout",
    summary="Завершение текущей сессии",
    description="Отзывает текущий refresh токен и очищает cookies. Не требует аутентификации.",
    responses={
        200: {
            "description": "Успешный выход",
            "content": {
                "application/json": {
                    "example": {"message": "Logged out successfully"}
                }
            }
        }
    }
)
async def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Завершение текущей сессии.
    Отзывает текущий refresh токен и очищает cookies.
    """
    # Извлекаем refresh токен из cookies
    refresh_token = request.cookies.get("refresh_token")
    
    if refresh_token:
        try:
            AuthManager.logout_user(db, refresh_token)
        except Exception:
            pass  # Игнорируем ошибки при выходе
    
    # Очищаем cookies
    clear_token_cookies(response)
    
    return {"message": "Logged out successfully"}


@router.post(
    "/logout-all",
    summary="Завершение всех сессий",
    description="Отзывает все refresh токены пользователя. Требует аутентификации.",
    responses={
        200: {
            "description": "Все сессии завершены",
            "content": {
                "application/json": {
                    "example": {
                        "message": "All sessions terminated",
                        "sessions_closed": 3
                    }
                }
            }
        },
        401: {
            "description": "Пользователь не аутентифицирован",
            "content": {
                "application/json": {
                    "example": {"detail": "Could not validate credentials"}
                }
            }
        },
        500: {
            "description": "Ошибка сервера",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to terminate sessions"}
                }
            }
        }
    }
)
async def logout_all(
    response: Response,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(AuthService.get_current_user)
):
    """
    Завершение всех сессий пользователя.
    Отзывает все refresh токены пользователя.
    """
    try:
        count = AuthManager.logout_all_user_sessions(db, current_user.id)
        
        # Очищаем cookies
        clear_token_cookies(response)
        
        return {
            "message": "All sessions terminated",
            "sessions_closed": count
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to terminate sessions"
        )


# OAuth 2.0 Endpoints

@router.get(
    "/oauth/{provider}",
    summary="Инициация OAuth входа",
    description="Перенаправляет на страницу авторизации OAuth провайдера (Yandex или VK).",
    responses={
        307: {
            "description": "Перенаправление на OAuth провайдера"
        },
        400: {
            "description": "Неподдерживаемый провайдер",
            "content": {
                "application/json": {
                    "example": {"detail": "Unsupported OAuth provider: google"}
                }
            }
        }
    }
)
async def oauth_initiate(provider: str):
    """
    Инициация входа через OAuth провайдера.
    """
    if provider == "yandex":
        auth_url = await OAuthService.yandex_get_auth_url()
        return RedirectResponse(url=auth_url)
    elif provider == "vk":
        auth_url = await OAuthService.vk_get_auth_url()
        return RedirectResponse(url=auth_url)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported OAuth provider: {provider}"
        )


@router.get(
    "/oauth/{provider}/callback",
    summary="OAuth Callback",
    description="Обработка ответа от OAuth провайдера. Получает код авторизации и создает сессию.",
    responses={
        200: {
            "description": "Успешная аутентификация через OAuth",
            "content": {
                "application/json": {
                    "example": {
                        "message": "OAuth login successful",
                        "user": {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "email": "user@yandex.ru",
                            "created_at": "2024-01-15T10:30:00",
                            "updated_at": "2024-01-15T10:30:00"
                        }
                    }
                }
            }
        },
        400: {
            "description": "Ошибка OAuth (invalid state, code и т.д.)",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid or expired state parameter"}
                }
            }
        }
    }
)
async def oauth_callback(
    provider: str,
    code: str,
    state: str,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Обработка ответа от OAuth провайдера.
    """
    # Проверяем state (защита от CSRF)
    if not OAuthService.validate_state(state, provider):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state parameter"
        )
    
    try:
        if provider == "yandex":
            # Обмениваем code на токен
            token_data = await OAuthService.yandex_exchange_code_for_token(code)
            if not token_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange code for token"
                )
            
            # Получаем данные пользователя
            user_info = await OAuthService.yandex_get_user_info(
                token_data["access_token"]
            )
            if not user_info:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get user info from Yandex"
                )
            
            # Извлекаем ID и email
            provider_id = user_info.get("id")
            email = user_info.get("default_email")
            
            if not provider_id or not email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid user info from Yandex"
                )
        
        elif provider == "vk":
            # Обмениваем code на токен
            token_data = await OAuthService.vk_exchange_code_for_token(code)
            if not token_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange code for token"
                )
            
            # Получаем данные пользователя
            user_id = token_data.get("user_id")
            user_info = await OAuthService.vk_get_user_info(
                token_data["access_token"],
                user_id
            )
            if not user_info:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get user info from VK"
                )
            
            # Извлекаем ID и email
            provider_id = str(user_id)
            email = user_info.get("email")
            
            if not provider_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid user info from VK"
                )
            
            # Если email не предоставлен, используем заглушку
            if not email:
                email = f"vk_{provider_id}@vk.oauth"
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported OAuth provider: {provider}"
            )
        
        # Находим или создаем пользователя
        user = OAuthService.find_or_create_oauth_user(
            db, provider, provider_id, email
        )
        
        # Создаем сессию (генерируем токены)
        access_token, refresh_token = OAuthService.create_oauth_session(db, user)
        
        # Устанавливаем токены в cookies
        create_token_response(response, access_token, refresh_token)
        
        # Для демонстрации возвращаем JSON:
        return {
            "message": "OAuth login successful",
            "user": UserResponse.model_validate(user)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth authentication failed"
        )


# Password Reset Endpoints

# Временное хранилище токенов сброса 
password_reset_tokens: Dict[str, Dict[str, Any]] = {}


@router.post(
    "/forgot-password",
    summary="Запрос сброса пароля",
    description="Генерирует токен сброса пароля. В production должен отправлять email, сейчас возвращает токен в ответе для тестирования.",
    responses={
        200: {
            "description": "Токен сброса сгенерирован",
            "content": {
                "application/json": {
                    "example": {
                        "message": "If the email exists, a reset link has been sent",
                        "reset_token": "AbC123XyZ_TokenHere"
                    }
                }
            }
        },
        400: {
            "description": "Ошибка валидации email",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid request data"}
                }
            }
        }
    }
)
async def forgot_password(
    reset_request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Запрос на сброс пароля.
    
    Генерирует токен сброса и "отправляет" его (возвращает в ответе для тестирования).
    """
    import secrets
    
    # Находим пользователя по email
    user = AuthManager.get_user_by_email(db, reset_request.email)
    
    # Если пользователь не найден, все равно возвращаем 200
    if not user:
        return {
            "message": "If the email exists, a reset link has been sent"
        }
    
    # Генерируем токен сброса
    reset_token = secrets.token_urlsafe(32)
    
    # Сохраняем токен с временем истечения (1 час)
    password_reset_tokens[reset_token] = {
        "user_id": str(user.id),
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=1)
    }
    
    # Для тестирования возвращаем токен в ответе:
    return {
        "message": "If the email exists, a reset link has been sent",
        "reset_token": reset_token
    }


@router.post(
    "/reset-password",
    summary="Установка нового пароля",
    description="Устанавливает новый пароль используя токен сброса. Токен одноразовый и истекает через 1 час.",
    responses={
        200: {
            "description": "Пароль успешно изменен",
            "content": {
                "application/json": {
                    "example": {"message": "Password has been reset successfully"}
                }
            }
        },
        400: {
            "description": "Недействительный или истекший токен",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid or expired reset token"}
                }
            }
        }
    }
)
async def reset_password(
    reset_data: PasswordReset,
    db: Session = Depends(get_db)
):
    """
    Установка нового пароля с использованием токена сброса.
    Проверяет валидность токена и обновляет пароль пользователя.
    """
    # Проверяем токен сброса
    if reset_data.token not in password_reset_tokens:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    token_data = password_reset_tokens[reset_data.token]
    
    # Проверяем время истечения
    if datetime.utcnow() > token_data["expires_at"]:
        # Удаляем просроченный токен
        del password_reset_tokens[reset_data.token]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )
    
    # Находим пользователя
    from uuid import UUID
    user = AuthManager.get_user_by_id(db, UUID(token_data["user_id"]))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    
    # Хешируем новый пароль и обновляем
    from app.utils.hashing import PasswordHasher
    user.password_hash = PasswordHasher.hash_password(reset_data.new_password)
    db.commit()
    
    # Удаляем использованный токен (одноразовый)
    del password_reset_tokens[reset_data.token]
    
    return {
        "message": "Password has been reset successfully"
    }
