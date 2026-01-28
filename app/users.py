import uuid
from jose import jwt ,JWTError
from fastapi import Depends,Request,APIRouter , HTTPException, status,Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import redis.asyncio as redis
from app.schemas  import UserRegister, UserLogin, VerifyRequest
from app.db import get_db
from datetime import datetime, timedelta
from dotenv import load_dotenv
from app.utils import send_verification_email
load_dotenv()
from pwdlib.hashers.argon2 import Argon2Hasher
import os
import json

hasher = Argon2Hasher()
Link = "https://cerbets.streamlit.app/"
redis_pool = redis.ConnectionPool.from_url(
    os.environ.get("REDIS_URL"),
    port=11626,
    password=os.environ.get("REDIS_PASSWORD"),
    decode_responses=True,
    socket_timeout=5,
    retry_on_timeout=True
)

async def get_redis():
    client = redis.Redis(connection_pool=redis_pool)
    try:
        yield client
    finally:
        await client.close()
SECRET = os.environ.get("JWT_PRIVATE_KEY")

ALGORITHM = "HS256"
router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)
#



async def rate_limit_by_ip(request: Request):
        return True
        ip = request.client.host
        if request.headers.get("X-Forwarded-For"):
            ip = request.headers.get("X-Forwarded-For").split(",")[0]
        key = f"rate_limit:user:{ip}"

        current_count = await r.incr(key)

        if current_count < 45 or  current_count > 40 :
            await r.expire(key, 3600)
        if current_count > 46 :
            ttl = await r.ttl(key)
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Lack of activity",
                    "retry_after_seconds": ttl
                }
            )


        return True


@router.get("/verify",)
async def verify_email(

        email: str = Query(...),
        code: str = Query(...),
        _=Depends(rate_limit_by_ip),
        conn=Depends(get_db),
r: redis.Redis = Depends(get_redis)
):
    try:
        pending_key = f"pending:user:{email}"
        pending_data = await r.hgetall(pending_key)

        if not pending_data:
            raise HTTPException(status_code=400, detail="Срок действия кода истек или регистрация не найдена")

        def decode_val(val):
            return val.decode("utf-8") if isinstance(val, bytes) else val

        stored_code = decode_val(pending_data.get("code"))
        stored_password = decode_val(pending_data.get("password"))

        if stored_code != code:
            raise HTTPException(status_code=400, detail="Неверный код подтверждения")

        try:

            query = "INSERT INTO users (email, hashed_password) VALUES ($1, $2) RETURNING id"
            user_id = await conn.fetchval(query, email, stored_password)

        except Exception as e:
            print(e)
            if "users_email_key" in str(e):
                raise HTTPException(status_code=400, detail="Пользователь уже зарегистрирован")
            raise e

        await r.delete(pending_key)

        return {"status": "ok", "message": "Account verified and created successfully", "id": user_id}

    except HTTPException as he:
        print(he)
        raise he
    except Exception as e:

        print(f"Error during verification: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/register", status_code=201)
async def register(user_data: UserRegister,      _=Depends(rate_limit_by_ip), conn=Depends(get_db)  , r: redis.Redis = Depends(get_redis)):
    hashed_pw = hasher.hash(user_data.password)
    query = "SELECT email FROM users WHERE email = $1"

    result = await conn.fetchval(query, user_data.email)
    if result:
        raise HTTPException(status_code=400, detail="User already registered")
    code = str(uuid.uuid4())
    pending_key = f"pending:user:{user_data.email}"
    pending_data = await r.hgetall(pending_key)
    if    pending_data:
        raise HTTPException(status_code=401, detail="User already registered")

    await r.hset(pending_key, mapping={
        "email": user_data.email,
        "password": hashed_pw,
        "code": code
    })
    await r.expire(pending_key, 900)

    verification_url = f"{Link}?email={user_data.email}&code={code}"
    await send_verification_email(verification_url, user_data.email)

    return {"message": "Verification email sent. Please verify to complete registration."}
@router.post("/login", status_code=200)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    conn=Depends(get_db)
,      _=Depends(rate_limit_by_ip),
r: redis.Redis = Depends(get_redis)
):
    try:
        user = await conn.fetchrow(
            "SELECT * FROM get_user_for_login($1)",
            form_data.username
        )
        if not user:
            raise HTTPException(status_code=400, detail="Wrong username or password")
        user_id = user["id"]
        user_profile_page = user["profile_page"]
        hashed_pw = user["hashed_password"]

        if not hasher.verify(form_data.password, hashed_pw):
            raise HTTPException(status_code=400, detail="Wrong username or password")

        expire = datetime.utcnow() + timedelta(minutes=30)
        payload = {
            "sub": str(user_id),
            "exp": expire
        }
        user_data = {
            "id": str(user["id"]),
            "mail":form_data.username,
            "profile_page": user_profile_page,
        }
        await r.setex(f"user:{user['id']}", 7200, json.dumps(user_data))
        token = jwt.encode(payload, SECRET, algorithm=ALGORITHM)

        return {
            "access_token": token,
            "token_type": "bearer",
            "id": str(user_id),
            "profile_page": user_profile_page,
        }


    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Login failed")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)  ,      _=Depends(rate_limit_by_ip), r: redis.Redis = Depends(get_redis)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        cached_user = await r.get(f"user:{user_id}")

        if cached_user:
            return json.loads(cached_user)
        return cached_user
    except JWTError:
        raise credentials_exception


#
# class UserManager(UUIDIDMixin,BaseUserManager[User,uuid.UUID]):
#     reset_password_token_url = SECRET
#     verification_token_secret = SECRET
#     async def on_after_register(
#         self, user: User, request: Optional[Request] = None  ) -> None:
#         print(f'User {user.id} has registered')
#     async def on_after_forgot_password(
#         self, user: User, token: str, request: Request | None = None
#     ) -> None:
#         print(f'User {user.id} has forgotten password')
#     async def on_after_reset_password(self, user: User, token: str, request: Request | None = None) -> None:
#         print(f'User {user.id} has forgotten password token')
#
# async def get_user_manager(user_db : SQLAlchemyUserDatabase = Depends(get_user_db)):
#     yield UserManager(user_db)
#
# bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")
# def get_jwt_strategy():
#     return JWTStrategy(secret=SECRET,lifetime_seconds=86400)
# auth_backend = AuthenticationBackend(
#     name= "jwt",
#     transport=bearer_transport,
#     get_strategy=get_jwt_strategy,
# )
# fastapi_users = FastAPIUsers[User,uuid.UUID](get_user_manager,[auth_backend])
# current_active_user = fastapi_users.current_user(active = True)
