import logging
from time import time
from typing import Dict, List, Optional, Tuple, Union

from auth0.v3.authentication import GetToken
from auth0.v3.authentication.revoke_token import RevokeToken
from auth0.v3.management.guardian import Guardian
from auth0.v3.management.users import Users
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, SecurityScopes
from fastapi_auth0 import Auth0, Auth0User
from jose import jwt

from fastapi_backend.config import ApplicationSettings
from fastapi_backend.schema import Auth0UsersList

settings = ApplicationSettings()
auth = Auth0(domain=settings.auth_domain, api_audience=settings.auth_audience)

__management_token: Optional[str] = None
__management_token_expire_date: Optional[int] = None
AUTH_DOMAIN_FULL = f"https://{settings.auth_domain}/"


class ExtendedAuth0User(Auth0User):
    anonymous: bool = False


def get_management_token() -> str:
    global __management_token, __management_token_expire_date
    if __management_token and time() < __management_token_expire_date:
        return __management_token
    token = GetToken(domain=settings.auth_domain)
    current_time = time()
    result = token.client_credentials(
        client_id=settings.auth_client_id,
        client_secret=settings.auth_client_secret,
        audience=f"https://{settings.auth_domain}/api/v2/",
    )
    __management_token = result["access_token"]
    __management_token_expire_date = (
        current_time + result["expires_in"] - 600
    )  # 10 minutes before the expire time
    return __management_token


def get_tokens(code: str, redirect_uri: str) -> Tuple[str, str]:
    token = GetToken(domain=settings.auth_domain)
    result = token.authorization_code(
        client_id=settings.auth_frontend_client_id,
        client_secret=settings.auth_frontend_client_secret,
        code=code,
        redirect_uri=redirect_uri,
    )
    return result["access_token"], result["refresh_token"]


def get_user_email(user_id: str) -> Optional[str]:
    mgmt_token = get_management_token()
    users = Users(domain=settings.auth_domain, token=mgmt_token)
    try:
        user = users.get(user_id, fields=["email"])
        return user["email"]
    except Exception as e:
        logging.error(e)
        return None


def get_user_profile(user_id: str) -> Optional[Dict[str, Optional[str]]]:
    mgmt_token = get_management_token()
    users = Users(domain=settings.auth_domain, token=mgmt_token)
    try:
        user = users.get(
            user_id, fields=["email", "family_name", "given_name", "name", "created_at"]
        )
        return {
            "email": user["email"],
            "family_name": user.get("family_name", None),
            "given_name": user.get("given_name", None),
            "name": user.get("name", None),
            "created_at": user["created_at"],
        }
    except Exception as e:
        get_apm_client().capture_exception()
        logging.error(e)
        return None


def revoke_refresh_token(refresh_token: str) -> None:
    revoke = RevokeToken(domain=settings.auth_domain)
    revoke.revoke_refresh_token(
        client_id=settings.auth_frontend_client_id, token=refresh_token
    )


def change_email(user_id: str, email: str):
    mgmt_token = get_management_token()
    users = Users(domain=settings.auth_domain, token=mgmt_token)
    users.update(
        user_id,
        {
            "email": email,
            "verify_email": True,
        },
    )


def list_users(
    fields: Optional[List[str]], page: int = 0, per_page: int = 50, _all=False
) -> Auth0UsersList:
    mgmt_token = get_management_token()
    users = Users(domain=settings.auth_domain, token=mgmt_token)
    if _all:
        _total = 0
        _page = 0
        _per_page = 50
        _users_list = []
        while True:
            _res = users.list(
                page=_page, per_page=_per_page, fields=fields, include_fields=True
            )
            _users_list.extend(_res["users"])
            _total += _res["length"]
            if _total == _res["total"]:
                break
            _page += 1

        return Auth0UsersList(
            start=0,
            limit=_total,
            length=_total,
            users=_users_list,
            total=_total,
        )

    return Auth0UsersList.parse_obj(
        users.list(page=page, per_page=per_page, fields=fields, include_fields=True)
    )


def enroll_user_to_mfa(user_id: str) -> str:
    mgmt_token = get_management_token()
    guardian = Guardian(domain=settings.auth_domain, token=mgmt_token)
    response = guardian.create_enrollment_ticket(
        {
            "user_id": user_id,
            "send_mail": False,
        }
    )
    return response["ticket_url"]


def OnlyOwner(user_id: str, user: Auth0User = Security(auth.get_user)):
    if user_id != user.id:
        raise HTTPException(403)
    return user


async def OptionalAuth(
    security_scopes: SecurityScopes,
    creds: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
):
    if not creds or not creds.credentials:
        return None
    return await auth.get_user(security_scopes, creds)


def AllowedPermissions(permissions: Union[str, List[str]]):
    if type(permissions) == str:
        permissions = [permissions]

    def allowed_permissions_dep(user: Auth0User = Security(auth.get_user)):
        user_permissions: List[str] = user.permissions or []
        for permission in permissions:
            if permission not in user_permissions:
                raise HTTPException(403, detail="Insufficient permissions")
        return user

    return allowed_permissions_dep


async def authenticate(
    security_scopes: SecurityScopes,
    creds: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer()),
):
    token = creds.credentials
    unverified_claims = jwt.get_unverified_claims(token)
    if unverified_claims["iss"] == settings.m2m_token_issuer:
        try:
            payload = jwt.decode(
                token, settings.m2m_token_secret, options={"verify_aud": False}
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Expired token")

        except jwt.JWTClaimsError as e:
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token claims (please check issuer and audience)",
            )

        except jwt.JWTError:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Malformed token")

        except Exception:
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED, detail="Error decoding token"
            )
        return Auth0User(**payload)
    elif unverified_claims["iss"] == AUTH_DOMAIN_FULL:
        return await auth.get_user(security_scopes, creds)
    else:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Unknown issuer")


def obfuscate_token(token: str) -> str:
    return f"{token[:4]}****{token[-4:]}"


async def AnonymousUserAuth(
    security_scopes: SecurityScopes,
    creds: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
) -> Auth0User:
    # if the Authorization token is not present, return an anonymous user
    # otherwise, validate the token and return the user
    if not creds or not creds.credentials:
        return ExtendedAuth0User(
            sub=settings.anonymous_user_id,
            email=settings.anonymous_user_email,
            permissions=[],
            anonymous=True,
        )
    return await auth.get_user(security_scopes, creds)


def is_anonymous_user(user: Auth0User) -> bool:
    if isinstance(user, ExtendedAuth0User):
        return user.anonymous
    return False
