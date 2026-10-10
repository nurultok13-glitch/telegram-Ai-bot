import logging
import time
from telegram import Update, BotCommand
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from telegram.constants import ChatAction, ParseMode, ChatType

from config import config
from database import db
from ai_providers import ai_manager
import utils

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    level=logging.INFO)
logger = logging.getLogger(__name__)


# ─── Command Handlers ───

async def start_cmd(update, ctx):
    user = update.effective_user
    await db.get_or_create_user(user.id, user.username or "",
                                user.first_name or "", user.last_name or "")
    await update.message.reply_text(
        "🤖 *Selamat Datang di AI Bot!*\n\n"
        "Saya bisa menjawab pertanyaan, menulis kode, "
        "menerjemahkan, dan banyak lagi!\n\n"
        "🚀 *Fitur:*\n"
        "• 💬 Chat AI (multi-model)\n"
        "• 🧠 Multiple AI Provider (GRATIS)\n"
        "• 💾 Riwayat tanpa batas\n"
        "• 📸 Analisis gambar\n\n"
        "Kirim pesan langsung untuk mulai!",
        parse_mode=ParseMode.MARKDOWN)


async def help_cmd(update, ctx):
    await update.message.reply_text(
        utils.help_text(), parse_mode=ParseMode.MARKDOWN)


async def model_cmd(update, ctx):
    uid = update.effective_user.id
    u = await db.get_or_create_user(uid)
    p = u.get("default_provider", "groq")
    m = u.get("default_model", "llama-3.1-70b")
    avail = ai_manager.available()
    lines = [f"🧠 *Ganti Model*\n\nAktif: `{p}/{m}`\n"]

    emojis = {"groq": "⚡", "gemini": "🔷", "openrouter": "🌐", "cerebras": "🚀"}
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    kb = []
    for prov in avail:
        models = ai_manager.models(prov)
        for mk in models:
            label = f"{emojis.get(prov, '🤖')} {mk}"
            if prov == p and mk == m:
                label += " ✅"
            kb.append([InlineKeyboardButton(label,
                       callback_data=f"sel:{prov}:{mk}")])
    kb.append([InlineKeyboardButton("🔙 Kembali", callback_data="back")])
    await update.message.reply_text(
        "\n".join(lines), parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(kb))


async def clear_cmd(update, ctx):
    n = await db.clear_history(update.effective_user.id)
    await update.message.reply_text(
        f"🗑️ *{n} pesan dihapus!*", parse_mode=ParseMode.MARKDOWN)


async def stats_cmd(update, ctx):
    s = await db.get_usage_stats(update.effective_user.id)
    e = utils.stats_emoji(s["total_messages"])
    await update.message.reply_text(
        f"📊 *Statistik* {e}\n\n"
        f"💬 Pesan: `{s['total_messages']}`\n"
        f"🔤 Tokens: `{s['total_tokens']}`\n"
        f"🧠 Provider: `{s['providers_used']}`\n"
        f"🎯 Model: `{s['models_used']}`",
        parse_mode=ParseMode.MARKDOWN)


async def history_cmd(update, ctx):
    h = await db.get_all_history(update.effective_user.id)
    if not h:
        await update.message.reply_text("📜 Belum ada riwayat.")
        return
    lines = [f"📜 *Riwayat ({len(h)} total)*\n"]
    for msg in h[-10:]:
        r = "🧑" if msg["role"] == "user" else "🤖"
        c = msg["content"][:80]
        if len(msg["content"]) > 80:
            c += "..."
        lines.append(f"{r} *{msg['role']}:* {c}")
    t = "\n".join(lines)
    await update.message.reply_text(t[:4000], parse_mode=ParseMode.MARKDOWN)


async def system_cmd(update, ctx):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    prompts = config.SYSTEM_PROMPTS
    emojis = {"default": "🤖", "coder": "👨‍💻", "creative": "🎨",
              "academic": "🎓", "general": "🌍"}
    kb = []
    for k in prompts:
        kb.append([InlineKeyboardButton(
            f"{emojis.get(k, '💬')} {k.title()}",
            callback_data=f"sys:{k}")])
    kb.append([InlineKeyboardButton("🔙 Kembali", callback_data="back")])
    await update.message.reply_text(
        "🎭 *Pilih Personality:*", parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(kb))


async def settings_cmd(update, ctx):
    u = await db.get_or_create_user(update.effective_user.id)
    await update.message.reply_text(
        f"⚙️ *Pengaturan*\n\n"
        f"📂 Provider: `{u.get('default_provider', 'groq')}`\n"
        f"🧠 Model: `{u.get('default_model', 'llama-3.1-70b')}`\n"
        f"🎭 Personality: `{u.get('system_prompt_mode', 'default')}`\n\n"
        f"Gunakan /model untuk ganti model",
        parse_mode=ParseMode.MARKDOWN)


async def version_cmd(update, ctx):
    avail = ai_manager.available()
    await update.message.reply_text(
        f"🚀 *Telegram AI Bot v2.0*\n\n"
        f"⚡ Providers: `{', '.join(avail)}`\n"
        f"💾 Database: SQLite (tanpa batas)\n"
        f"💰 Cost: $0.00",
        parse_mode=ParseMode.MARKDOWN)


# ─── AI Chat Handler ───

async def handle_msg(update, ctx):
    if update.effective_chat.type == ChatType.BOT:
        return
    user = update.effective_user
    text = update.message.text
    if not text or not text.strip():
        return

    udata = await db.get_or_create_user(
        user.id, user.username or "", user.first_name or "", user.last_name or "")
    if udata.get("is_banned"):
        await update.message.reply_text("🚫 Akun diblokir.")
        return

    await ctx.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    await db.save_message(user.id, "user", text)
    history = await db.get_history(user.id)

    provider = udata.get("default_provider", "groq")
    model = udata.get("default_model", "llama-3.1-70b")
    pmode = udata.get("system_prompt_mode", "default")
    sprompt = config.SYSTEM_PROMPTS.get(pmode, config.SYSTEM_PROMPTS["default"])

    msgs = [{"role": "system", "content": sprompt}]
    for h in history:
        if h["role"] in ("user", "assistant"):
            msgs.append({"role": h["role"], "content": h["content"]})

    try:
        result = await ai_manager.chat(provider, msgs, model)
        if "error" in result:
            await update.message.reply_text(
                utils.get_error_message(result["error"]),
                parse_mode=ParseMode.MARKDOWN)
            return

        resp = result.get("response", "")
        if not resp:
            await update.message.reply_text(
                "❌ Model tidak memberi respons. Coba lagi.")
            return

        await db.save_message(user.id, "assistant", resp,
                              provider, model, result.get("tokens_used", 0))
        await db.log_usage(user.id, provider, model,
                           result.get("tokens_input", 0),
                           result.get("tokens_output", 0),
                           result.get("response_time", 0))

        resp = utils.format_response(resp)
        for chunk in utils.split_message(resp):
            try:
                await update.message.reply_text(chunk, parse_mode=ParseMode.MARKDOWN)
            except Exception:
                await update.message.reply_text(chunk)

    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def handle_photo(update, ctx):
    """Analisis gambar dengan Gemini Vision."""
    import base64, aiohttp
    user = update.effective_user
    caption = update.message.caption or "Analisis gambar ini"
    udata = await db.get_or_create_user(
        user.id, user.username or "", user.first_name or "")

    photo = update.message.photo[-1]
    file = await ctx.bot.get_file(photo.file_id)
    file_bytes = bytes(await file.download_as_bytearray())

    await ctx.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    if config.GEMINI_API_KEY:
        model = "gemini-1.5-flash"
        url = (f"https://generativelanguage.googleapis.com/v1beta"
               f"/models/{model}:generateContent?key={config.GEMINI_API_KEY}")
        payload = {"contents": [{"parts": [
            {"text": caption},
            {"inline_data": {"mime_type": "image/jpeg",
                             "data": base64.b64encode(file_bytes).decode()}}]}],
            "generationConfig": {"maxOutputTokens": 4096, "temperature": 0.7}}

        async with aiohttp.ClientSession() as s:
            async with s.post(url, json=payload) as r:
                d = await r.json()
                try:
                    resp = d["candidates"][0]["content"]["parts"][0]["text"]
                except Exception:
                    resp = f"Error: {d.get('error', {}).get('message', 'Unknown')}"

        await db.save_message(user.id, "user", f"[📷 Foto] {caption}")
        await db.save_message(user.id, "assistant", resp, "gemini", model)

        for chunk in utils.split_message(utils.format_response(resp)):
            try:
                await update.message.reply_text(chunk, parse_mode=ParseMode.MARKDOWN)
            except Exception:
                await update.message.reply_text(chunk)
    else:
        await update.message.reply_text(
            "📷 Kirim analisis: Gemini API key belum di-set.")


# ─── Callback Handler (Tombol Inline) ───

async def cb_handler(update, ctx):
    q = update.callback_query
    await q.answer()
    data = q.data
    uid = q.from_user.id

    if data == "back":
        await q.edit_message_text(
            "🤖 *Menu Utama*\n\nKirim pesan untuk chat dengan AI!",
            parse_mode=ParseMode.MARKDOWN)

    elif data.startswith("sel:"):
        parts = data.split(":")
        prov, model = parts[1], parts[2]
        await db.update_user(uid, default_provider=prov, default_model=model)
        await q.edit_message_text(
            f"✅ Model: `{model}`\nProvider: `{prov}`",
            parse_mode=ParseMode.MARKDOWN)

    elif data.startswith("sys:"):
        pmode = data.split(":")[1]
        if pmode in config.SYSTEM_PROMPTS:
            await db.update_user(uid, system_prompt_mode=pmode)
            await q.edit_message_text(
                f"✅ Personality: `{pmode}`",
                parse_mode=ParseMode.MARKDOWN)

    else:
        await q.answer("Tidak dikenal!", show_alert=True)


# ─── Startup ───

async def post_init(app):
    await db.initialize()
    cmds = [
        BotCommand("start", "🚀 Mulai"), BotCommand("help", "❓ Bantuan"),
        BotCommand("model", "🧠 Ganti model"), BotCommand("clear", "🗑️ Hapus riwayat"),
        BotCommand("stats", "📊 Statistik"), BotCommand("history", "📜 Riwayat"),
        BotCommand("system", "🎭 Personality"), BotCommand("settings", "⚙️ Settings"),
        BotCommand("version", "ℹ️ Versi"),
    ]
    await app.bot.set_my_commands(cmds)
    print(f"\n🚀 Bot ONLINE! Providers: {ai_manager.available()}\n")


def main():
    if not config.TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN belum di-set!")
        return
    if not ai_manager.available():
        print("❌ Tidak ada API key! Set minimal 1.")
        return

    app = (ApplicationBuilder()
           .token(config.TELEGRAM_BOT_TOKEN)
           .post_init(post_init)
           .build())

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("model", model_cmd))
    app.add_handler(CommandHandler("clear", clear_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("history", history_cmd))
    app.add_handler(CommandHandler("system", system_cmd))
    app.add_handler(CommandHandler("settings", settings_cmd))
    app.add_handler(CommandHandler("version", version_cmd))
    app.add_handler(CallbackQueryHandler(cb_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("🚀 Bot berjalan...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
