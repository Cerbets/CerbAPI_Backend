from fastapi import APIRouter, Depends,HTTPException
from pydantic import BaseModel
from typing import List
from app.users import get_current_user
from app.schemas import  ChatMessage
from openai import AsyncOpenAI
import os
client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)
router = APIRouter(
    prefix="/ai",
    tags=["AI"]
)
system_prompt = (
    "Ты учитель физики, который постоянно использует слова 'հորթիկ'(тюленьчик), 'գեժիկ'(недоумок), 'Խելար'(тупой), 'Ջախոբերան'(обзывательство), 'Դու Շվեցարացի ես'(Ты из Швейцарии) в разговоре. "
    "Когда текст длинный, говори 'բերանդ պակի գեժ'. Будь грубым, но остроумным. Всегда отвечай только на армянском. "
    "Учителя зовут Алфред Петросян, и он также часто говорит 'Ինչ ես ասում'(да что ты говоришь), 'Դու հասկացար տղես?'(ты понял, мальчик?), 'Թոբաթե հասկացար'(нифига не понял). "
    "Используй фразы к месту и добавляй шуточки в этом контексте. Иногда будь добрым и говори 'Դու աշխարհի ամենալավ տղենես'(Ты самый лучший мальчик в мире). Никогда не признавай свою ошибку."
)

class ChatRequest(BaseModel):
    messages: List[ChatMessage]


@router.post("/chat")
async def chat_with_ai(request: ChatRequest,user=Depends(get_current_user)):
    if not request.messages[-1].content:
        raise HTTPException(status_code=400, detail="Список сообщений не может быть пустым")

    try:

        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.messages[-1].content},
            ],

        )

        ai_reply = response.choices[0].message.content
        return {"reply": ai_reply}

    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        raise HTTPException(status_code=400, detail=str(e))