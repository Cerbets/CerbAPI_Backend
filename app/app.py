from fastapi import FastAPI ,HTTPException,Depends, Form, UploadFile , File, APIRouter, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from app.users import get_current_user
from app.db import  db, get_db
from app.users import router as users_router
from contextlib import asynccontextmanager
from app.schemas import User
import os
import shutil
import tempfile
from pathlib import Path
from app.images import imagekit
from app.ai import router as ai_router
import redis.asyncio as redis
import json
from app.users import get_redis
@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    yield
    await db.disconnect()
SHOW_DOCS = os.getenv("ENV") != "production"
app = FastAPI(lifespan=lifespan,
docs_url = "/docs" if SHOW_DOCS else None,
redoc_url = "/redoc" if SHOW_DOCS else None,
openapi_url = "/openapi.json" if SHOW_DOCS else None,
redirect_slashes=False
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
from app.messages import router as messages_router
from app.websocket import manager
#from app.websocket_router import ws_router # используй новое имя

app.include_router(messages_router)
#app.include_router(ws_router)

app.include_router(
    users_router,

)
app.include_router(
    ai_router,
    dependencies=[Depends(get_current_user)]
)
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):

    print("🚀 КЛИЕНТ ПОДКЛЮЧИЛСЯ!")
    try:
        await manager.connect(websocket)

        while True:
                # Ждем сообщение от клиента (даже если он ничего не шлет)
                data = await websocket.receive_text()
                print(f"📩 Пришло от фронта: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("🔌 Клиент отключился по-хорошему")
    except Exception as e:
        print(f"🔌 Отключено: {e}")


@app.post("/upload")
async def upload_file(
        file: UploadFile = File(...),
        caption: str = Form(""),
        user: User = Depends(get_current_user),
        session: str = Depends(get_db)
):
    temp_file_path = None
    try:

        suffix = os.path.splitext(file.filename)[1]

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file_path = temp_file.name
            shutil.copyfileobj(file.file, temp_file)

        upload_result = await imagekit.files.upload(
            file=Path(temp_file_path),
            file_name=file.filename,
            use_unique_file_name=True,
            tags=["backend-upload"]
        )
        print(user)
        print(user["id"])
        print(upload_result.url)
        print(caption)
       # post = Post(user_id = user,caption=caption, url=upload_result.url, file_name=file.filename, file_type=suffix)
        result = await session.fetchrow(
            "SELECT * FROM add_post($1::uuid,$2,$3)",
            user["id"],upload_result.url,caption
        )

        return result

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        await file.close()


@app.get("/feed")
async def get_feed(
        conn: str = Depends(get_db),
        current_user_id: User = Depends(get_current_user)
):
    query = """
            SELECT posts.id, \
                   posts.userid, \
                   posts.url, \
                   posts.caption, \
                   posts.created_at, \
                   users.email
            FROM posts 
                     JOIN users  ON posts.userid = users.id
            ORDER BY posts.created_at DESC \
            """

    rows = await conn.fetch(query)

    posts_data = []
    for row in rows:
        posts_data.append({
            "id": str(row["id"]),
            "user_id": str(row["userid"]),
            "url": row["url"],
            "caption": row["caption"],
            "created_at": row["created_at"].isoformat(),
            "email": row["email"],
            "is_owner": str(row["userid"]) == str(current_user_id)
        })

    return {"posts": posts_data}


@app.delete("/posts/{post_id}")
async def delete_post(
        post_id: str,
        conn: str = Depends(get_db),
        current_user_id: User = Depends(get_current_user)
):
    query_check = "SELECT userid FROM posts WHERE id = $1::uuid"
    post = await conn.fetchrow(query_check, post_id)

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if str(post["userid"]) != str(current_user_id):
        raise HTTPException(
            status_code=403,
            detail="You don't have access to delete this post"
        )

    await conn.execute("DELETE FROM posts WHERE id = $1::uuid", post_id)

    return {"success": True, "message": "Post deleted successfully"}


@app.post("/profile_update")
async def upload_file(
        file: UploadFile = File(...),
        user: User = Depends(get_current_user),
        session: str = Depends(get_db),
r: redis.Redis = Depends(get_redis)
):
    temp_file_path = None
    try:
        suffix = os.path.splitext(file.filename)[1]
        cached_user = await r.get(f"user:{user['id']}")

        if cached_user:
            cached_user =  json.loads(cached_user)

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file_path = temp_file.name
            shutil.copyfileobj(file.file, temp_file)
        upload_result = await imagekit.files.upload(
            file=Path(temp_file_path),
            file_name=file.filename,
            use_unique_file_name=True,
            tags=["backend-upload"]
        )
        cached_user["profile_page"] = upload_result.url
        print(cached_user)
        row= await session.fetchrow(
            "SELECT * FROM change_user_profile_page_link($1::uuid, $2)",
            user['id'],
            upload_result.url
        )
        print(row)
        if not row:
            raise HTTPException(status_code=400, detail=str("ID NOT FOUND"))
        await r.setex(f"user:{user['id']}", 7200, json.dumps(cached_user))

        return {"url" :upload_result.url }

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        await file.close()





#----/trash/-------

# from sqlalchemy.ext.asyncio import AsyncSession
# from app.schemas import PostCreate,PostResponse, UserCreate, UserUpdate, UserRead

# from websockets import connect

# from sqlalchemy import select
# from app.images import imagekit
# from pathlib import Path
# import shutil
# import os
# import uuid
# import tempfile
# from app.users import auth_backend, current_active_user,fastapi_users
# from app.ai import router as ai_router

# app.include_router(fastapi_users.get_auth_router(auth_backend),prefix="/auth/jwt",tags=["auth"])
# app.include_router(fastapi_users.get_register_router(UserRead,UserCreate),prefix="/auth",tags=["auth"])
# app.include_router(fastapi_users.get_reset_password_router(),prefix="/auth",tags=["auth"])
# app.include_router(fastapi_users.get_verify_router(UserRead),prefix="/auth",tags=["auth"])
# app.include_router(fastapi_users.get_users_router(UserRead,UserUpdate),prefix="/users",tags=["auth"])
# app.include_router(
#     ai_router,
#     dependencies=[Depends(current_active_user)] # Теперь все роуты в ai.py защищены!
# )
#

#
# @app.post("/profile_update")
# async def upload_file(
#         file: UploadFile = File(...),
#         user: User = Depends(current_active_user),
#         session: AsyncSession = Depends(get_async_session)
# ):
#     temp_file_path = None
#     try:
#         suffix = os.path.splitext(file.filename)[1]
#         result = await session.execute(select(Set_Profile_page).filter_by(user_id=user.id))
#         old_profile = result.scalar_one_or_none()
#         if old_profile:
#             await session.delete(old_profile)
#             await session.flush()
#         with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
#             temp_file_path = temp_file.name
#             shutil.copyfileobj(file.file, temp_file)
#
#         upload_result = await imagekit.files.upload(
#             file=Path(temp_file_path),
#             file_name=file.filename,
#             use_unique_file_name=True,
#             tags=["backend-upload"]
#         )
#
#         post = Set_Profile_page(user_id = user.id, url=upload_result.url, file_name=file.filename, file_type=suffix)
#         session.add(post)
#         await session.commit()
#         await session.refresh(post)
#         return post
#
#     except Exception as e:
#         print(f"Error: {e}")
#         return {"error": str(e)}
#
#     finally:
#         if temp_file_path and os.path.exists(temp_file_path):
#             os.unlink(temp_file_path)
#         await file.close()
#
#
#
#
#
#
#

#