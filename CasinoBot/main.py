import asyncio
import hashlib
import hmac
import json
import random
import time
import datetime
from contextlib import asynccontextmanager
from urllib.parse import parse_qsl

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from bot import bot, start_bot, RATE, STAR_PACKS
from database import (
    get_balance, add_balance, set_balance, create_withdrawal,
    get_top_players, get_user_full_stats,
    get_user_achievements, ACHIEVEMENTS,
    get_referral_stats, get_discount,
    log_game, unlock_achievement,
    get_promo, promo_already_used, use_promo,
    get_daily_info, claim_daily,
    ensure_user,
    get_stats, get_last_withdrawals, update_withdrawal,
    get_user_by_username, get_all_user_ids,
    create_promo, delete_promo, list_promos,
    log_admin_action, get_admin_logs,
    log_visit, can_withdraw,
)

WITHDRAW_RATE = 100
MIN_WITHDRAW = 15
BETS = [10, 50, 100, 500, 1000, 10000, 20000, 30000, 50000, 100000]
ADMIN_IDS = [7643224285]


def validate_init_data(init_data: str) -> dict:
    if not init_data:
        raise HTTPException(401, "no_init_data")
    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise HTTPException(401, "no_hash")
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret_key = hmac.new(b"WebAppData", bot.token.encode(), hashlib.sha256).digest()
    computed = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed, received_hash):
        raise HTTPException(401, "invalid_signature")
    return json.loads(pairs.get("user", "{}"))


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def admin_only(init_data: str) -> dict:
    user = validate_init_data(init_data)
    if not is_admin(user["id"]):
        raise HTTPException(403, "no_access")
    return user


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(start_bot())
    print("🚀 Бот и веб-сервер запущены")
    yield
    task.cancel()


app = FastAPI(lifespan=lifespan)

# ═══════════ API (все твои эндпоинты) ═══════════
# (Весь блок API от /api/profile до /api/admin/broadcast ОСТАЕТСЯ БЕЗ ИЗМЕНЕНИЙ, я его не дублирую, чтобы не тратить твое время, он есть в твоем файле. ОН НЕ МЕНЯЕТСЯ.)

# ... (вставь сюда свои API эндпоинты из файла) ...

# ⚠️ НОВЫЙ МАРШРУТ ДЛЯ ИГРЫ (ВМЕСТО /webapp) ⚠️
@app.get("/play")
async def serve_play():
    return FileResponse("webapp/index.html")

# ⚠️ РАЗДАЧА CSS/JS ИЗ КОРНЯ ⚠️
app.mount("/", StaticFiles(directory="webapp"), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
