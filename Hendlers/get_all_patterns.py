from typing import List, Optional, Any, Dict, Tuple, Union

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import CHAT_PROCESS_SERVICE_URL
from external_service import make_request

PAGE_SIZE = 10
get_all_patterns_router = Router()
STATE: Dict[Tuple[int, int], List[Optional[Union[str, int]]]] = {}

class TextsPageCD(CallbackData, prefix="txt"):
    page: int

def build_keyboard(page: int, has_prev: bool, has_next: bool) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    row: List[InlineKeyboardButton] = []
    if has_prev:
        row.append(InlineKeyboardButton(text="⟨ Back", callback_data=TextsPageCD(page=page - 1).pack()))
    row.append(InlineKeyboardButton(text=f"{page + 1}", callback_data="noop"))
    if has_next:
        row.append(InlineKeyboardButton(text="Next ⟩", callback_data=TextsPageCD(page=page + 1).pack()))
    kb.row(*row)
    return kb

def render_page_text(items: List[Dict[str, Any]], page: int) -> str:
    if not items and page == 0:
        return "No Patterns"
    if not items:
        return 'No Patterns'
    start_idx = page * PAGE_SIZE + 1
    lines = [f"Patterns — page {page + 1}:"]
    for i, item in enumerate(items, start=start_idx):
        q = str(item.get("question") or item.get("id") or "")
        text = f'❔ <b>Question:</b> {q}\n💬 <b>Answer:</b> {item.get("answer") or ""}'
        lines.append(f"  <b>{i}</b>.\n{text}\n")
    return "\n".join(lines)

def normalize_response(raw: Any) -> tuple[List[Dict[str, Any]], Optional[Union[str, int]]]:
    if isinstance(raw, dict):
        data = raw.get("body", raw)
        if isinstance(data, dict):
            items = data.get("items") or data.get("results") or data.get("data") or []
            nxt = data.get("next") or data.get("next_page_offset") or None
            return list(items), nxt
        if isinstance(data, list):
            return list(data), None
    if isinstance(raw, list):
        return list(raw), None
    return [], None

async def fetch_page(cursor: Optional[Union[str, int]]) -> tuple[List[Dict[str, Any]], Optional[Union[str, int]]]:
    params: Dict[str, Any] = {"limit": PAGE_SIZE}
    if cursor is not None:
        params["cursor"] = cursor
    raw = await make_request(base_url=CHAT_PROCESS_SERVICE_URL, url="pattern/get-all-texts", params=params)
    return normalize_response(raw)

@get_all_patterns_router.message(Command("get_all_patterns"))
async def get_all_texts_cmd(message: Message):
    page = 0
    items, nxt = await fetch_page(None)
    has_prev = False
    has_next = nxt is not None and len(items) > 0
    text = render_page_text(items, page)
    kb = build_keyboard(page, has_prev, has_next)
    sent = await message.answer(text=text, reply_markup=kb.as_markup())
    key = (sent.chat.id, sent.message_id)
    STATE[key] = [None]
    if has_next:
        STATE[key].append(nxt)

@get_all_patterns_router.callback_query(TextsPageCD.filter())
async def paginate_texts(callback: CallbackQuery, callback_data: TextsPageCD):
    msg = callback.message
    key = (msg.chat.id, msg.message_id)
    if key not in STATE:
        STATE[key] = [None]
    page = max(0, callback_data.page)
    if page >= len(STATE[key]):
        page = len(STATE[key]) - 1
    cursor = STATE[key][page]
    items, nxt = await fetch_page(cursor)
    if len(STATE[key]) == page + 1 and nxt is not None:
        STATE[key].append(nxt)
    has_prev = page > 0
    has_next = (len(STATE[key]) > page + 1) or (nxt is not None)
    text = render_page_text(items, page)
    kb = build_keyboard(page, has_prev, has_next)
    await msg.edit_text(text=text, reply_markup=kb.as_markup())
    await callback.answer()

@get_all_patterns_router.callback_query(F.data == "noop")
async def noop_cb(callback: CallbackQuery):
    await callback.answer()
