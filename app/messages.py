from fastapi import Depends,Request,APIRouter , HTTPException, status,Query
from app.users import get_current_user
from app.db import get_db
from app.schemas import  ChatMessage,Messageid
from app.websocket import manager
router = APIRouter(
    prefix="/messages",
    tags=["messages"],
)
@router.get("/")
async def get_messages(
    conn = Depends(get_db),
    current_user = Depends(get_current_user)
):
    my_id = current_user["id"] if isinstance(current_user, dict) else current_user.id

    query = """
            SELECT messages.id, 
                   messages.content, 
                   messages.user_id, 
                   messages.created_at, 
                   users.email
            FROM messages 
            JOIN users ON messages.user_id = users.id
            ORDER BY messages.created_at DESC 
            LIMIT 50
            """

    rows = await conn.fetch(query)

    messages_data = []
    for row in rows:
        messages_data.append({
            "id": row["id"],
            "content": row["content"],
            "user_id": str(row["user_id"]),
            "email": row["email"],
            "created_at": row["created_at"].isoformat(),
            "is_owner": str(row["user_id"]) == str(my_id)
        })

    return {"messages": messages_data}

@router.post("/")
async def upload_message(message : ChatMessage, current_user: dict = Depends(get_current_user), session: str = Depends(get_db)  ):
    result = await session.fetchrow(
        "SELECT * FROM add_message($1::uuid,$2)",
        current_user["id"], message.content
    )
    print(current_user)
    if result:
        new_message_data = {
            "id": result["add_message"],
            "content": message.content,
            "email": current_user["mail"],
            "user_id": str(current_user["id"]),
            "created_at": "SENT VIA WEBSOCKET",
            "is_owner": False
        }
        print("📣 [WS] Вызов manager.broadcast...")
        await manager.broadcast(new_message_data)

    return result
@router.delete("/")
async def delete_message(id : Messageid, current_user: dict = Depends(get_current_user), session: str = Depends(get_db)  ):
    result = await session.fetchrow(
        "SELECT * FROM delete_message($1::bigint,$2::uuid)",
        id.message_id,  current_user["id"]
    )
    return result

