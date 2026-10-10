def split_message(text, max_len=4096):
    if len(text) <= max_len:
        return [text]
    msgs, remaining = [], text
    while remaining:
        if len(remaining) <= max_len:
            msgs.append(remaining)
            break
        chunk = remaining[:max_len]
        code_open = chunk.count("```")
        pos = max_len
        if code_open % 2 == 1:
            lc = chunk.rfind("```")
            if lc > 100:
                msgs.append(remaining[:lc].rstrip())
                remaining = remaining[lc:].lstrip()
                continue
        for sep in ["\n\n", "\n", ". "]:
            p = chunk.rfind(sep)
            if p > max_len // 4:
                pos = p + len(sep)
                break
        msgs.append(remaining[:pos].rstrip())
        remaining = remaining[pos:].lstrip()
    return msgs


def format_response(text):
    if len(text) > 60000:
        text = text[:60000] + "\n\n... *(dipotong)*"
    return text


def get_error_message(error):
    if "rate" in error.lower() or "429" in error:
        return "⚠️ *Rate Limit!* Tunggu sebentar.\n`" + error[:200] + "`"
    elif "key" in error.lower() or "401" in error:
        return "🔑 *API Key Error!* Cek Environment Variables."
    elif "connection" in error.lower():
        return "🌐 *Connection Error!* Coba lagi nanti."
    return "❌ *Error:* `" + error[:300] + "`"


def stats_emoji(t):
    if t > 1000: return "🏆"
    if t > 500: return "🌟"
    if t > 100: return "💎"
    if t > 10: return "✅"
    return "🔰"


def help_text():
    return (
        "❓ *Bantuan AI Bot v2.0*\n\n"
        "🤖 *Saya bisa:*\n"
        "• Menjawab pertanyaan apapun\n"
        "• Menulis & menjelaskan kode\n"
        "• Menerjemahkan bahasa\n"
        "• Menganalisis gambar\n"
        "• Meringkas dokumen\n\n"
        "💡 *Tips:*\n"
        "• Kirim pesan langsung untuk chat\n"
        "• `/model` untuk ganti model\n"
        "• `/clear` untuk reset chat\n"
        "• Kirim foto untuk analisis"
    )


def commands_help():
    return (
        "⌨️ *Commands:*\n\n"
        "`/start` — Mulai\n"
        "`/help` — Bantuan\n"
        "`/model` — Ganti model\n"
        "`/settings` — Pengaturan\n"
        "`/system` — Personality\n"
        "`/clear` — Hapus riwayat\n"
        "`/stats` — Statistik\n"
        "`/history` — Riwayat chat\n"
        "`/version` — Info versi"
    )


def troubleshoot():
    return (
        "🔧 *Troubleshooting:*\n\n"
        "❌ Bot tidak respon? → Tunggu 10 detik\n"
        "❌ Rate Limit? → Tunggu 30 detik\n"
        "❌ API Key Error? → Cek Environment Variables\n"
        "❌ Lambat? → Ganti ke Groq (paling cepat)"
    )
