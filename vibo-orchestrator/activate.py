"""ViBo skill activation (run by the buyer once).

Usage:
    python3 activate.py VIBO-XXXX-XXXX-XXXX-XXXX   # paid key
    python3 activate.py --email you@mail.com        # free 2-day trial
    python3 activate.py --help                      # this help
    python3 activate.py --lang <code> ...           # messages in your language

Supported languages (--lang): en, zh, hi, es, fr, ar, pt, ru, ja, de.
Language is auto-detected from the system locale; override with --lang
or the VIBO_LANG environment variable.

Creates vibo_license.dat next to the skill. After activation
the skill works only on this machine.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from license import activate  # noqa: E402

LICENSE_PATH = Path(__file__).parent / "vibo_license.dat"

# ── i18n: 10 major languages ──────────────────────────────────────────────
LANGS = ["en", "zh", "hi", "es", "fr", "ar", "pt", "ru", "ja", "de"]

T = {
    "usage": {
        "en": "Usage:",
        "zh": "用法：",
        "hi": "उपयोग:",
        "es": "Uso:",
        "fr": "Utilisation :",
        "ar": "الاستخدام:",
        "pt": "Uso:",
        "ru": "Использование:",
        "ja": "使い方:",
        "de": "Verwendung:",
    },
    "usage_key": {
        "en": "  python3 activate.py VIBO-XXXX-XXXX-XXXX-XXXX   # paid key",
        "zh": "  python3 activate.py VIBO-XXXX-XXXX-XXXX-XXXX   # 付费密钥",
        "hi": "  python3 activate.py VIBO-XXXX-XXXX-XXXX-XXXX   # सशुल्क कुंजी",
        "es": "  python3 activate.py VIBO-XXXX-XXXX-XXXX-XXXX   # clave de pago",
        "fr": "  python3 activate.py VIBO-XXXX-XXXX-XXXX-XXXX   # clé payante",
        "ar": "  python3 activate.py VIBO-XXXX-XXXX-XXXX-XXXX   # مفتاح مدفوع",
        "pt": "  python3 activate.py VIBO-XXXX-XXXX-XXXX-XXXX   # chave paga",
        "ru": "  python3 activate.py VIBO-XXXX-XXXX-XXXX-XXXX   # платный ключ",
        "ja": "  python3 activate.py VIBO-XXXX-XXXX-XXXX-XXXX   # 有料キー",
        "de": "  python3 activate.py VIBO-XXXX-XXXX-XXXX-XXXX   # bezahlter Schlüssel",
    },
    "usage_email": {
        "en": "  python3 activate.py --email you@mail.com        # free 2-day trial",
        "zh": "  python3 activate.py --email you@mail.com        # 免费2天试用",
        "hi": "  python3 activate.py --email you@mail.com        # मुफ्त 2-दिन परीक्षण",
        "es": "  python3 activate.py --email you@mail.com        # prueba gratis 2 días",
        "fr": "  python3 activate.py --email you@mail.com        # essai gratuit 2 jours",
        "ar": "  python3 activate.py --email you@mail.com        # تجربة مجانية يومين",
        "pt": "  python3 activate.py --email you@mail.com        # teste grátis 2 dias",
        "ru": "  python3 activate.py --email you@mail.com        # бесплатный триал 2 дня",
        "ja": "  python3 activate.py --email you@mail.com        # 2日間無料トライアル",
        "de": "  python3 activate.py --email you@mail.com        # 2 Tage kostenlos testen",
    },
    "usage_lang": {
        "en": "  python3 activate.py --lang <code> ...           # messages in your language",
        "zh": "  python3 activate.py --lang <code> ...           # 以您的语言显示消息",
        "hi": "  python3 activate.py --lang <code> ...           # आपकी भाषा में संदेश",
        "es": "  python3 activate.py --lang <code> ...           # mensajes en tu idioma",
        "fr": "  python3 activate.py --lang <code> ...           # messages dans votre langue",
        "ar": "  python3 activate.py --lang <code> ...           # رسائل بلغتك",
        "pt": "  python3 activate.py --lang <code> ...           # mensagens no seu idioma",
        "ru": "  python3 activate.py --lang <code> ...           # сообщения на вашем языке",
        "ja": "  python3 activate.py --lang <code> ...           # あなたの言語で表示",
        "de": "  python3 activate.py --lang <code> ...           # Nachrichten in Ihrer Sprache",
    },
    "activated": {
        "en": "✅ License activated for this machine.",
        "zh": "✅ 许可证已为本机激活。",
        "hi": "✅ इस मशीन के लिए लाइसेंस सक्रिय हो गया।",
        "es": "✅ Licencia activada para esta máquina.",
        "fr": "✅ Licence activée pour cette machine.",
        "ar": "✅ تم تفعيل الترخيص لهذا الجهاز.",
        "pt": "✅ Licença ativada para esta máquina.",
        "ru": "✅ Лицензия активирована для этой машины.",
        "ja": "✅ このマシンでライセンスが有効になりました。",
        "de": "✅ Lizenz für diesen Computer aktiviert.",
    },
    "activation_failed": {
        "en": "❌ Activation failed:",
        "zh": "❌ 激活失败：",
        "hi": "❌ सक्रियण विफल:",
        "es": "❌ Activación fallida:",
        "fr": "❌ Échec de l'activation :",
        "ar": "❌ فشل التفعيل:",
        "pt": "❌ Falha na ativação:",
        "ru": "❌ Ошибка активации:",
        "ja": "❌ アクティベーションに失敗:",
        "de": "❌ Aktivierung fehlgeschlagen:",
    },
    "key_not_found": {
        "en": "Key not found. Check the key or buy a license at https://wwwvibo.com",
        "zh": "未找到密钥。请检查密钥或在 https://wwwvibo.com 购买许可证",
        "hi": "कुंजी नहीं मिली। कुंजी जांचें या https://wwwvibo.com पर लाइसेंस खरीदें",
        "es": "Clave no encontrada. Revise la clave o compre una licencia en https://wwwvibo.com",
        "fr": "Clé introuvable. Vérifiez la clé ou achetez une licence sur https://wwwvibo.com",
        "ar": "المفتاح غير موجود. تحقق من المفتاح أو اشترِ ترخيصًا من https://wwwvibo.com",
        "pt": "Chave não encontrada. Verifique a chave ou compre uma licença em https://wwwvibo.com",
        "ru": "Ключ не найден. Проверьте ключ или купите лицензию на https://wwwvibo.com",
        "ja": "キーが見つかりません。キーを確認するか、https://wwwvibo.com でライセンスを購入してください",
        "de": "Schlüssel nicht gefunden. Prüfen Sie den Schlüssel oder kaufen Sie eine Lizenz auf https://wwwvibo.com",
    },
    "trial_activated": {
        "en": "✅ Free trial activated for",
        "zh": "✅ 免费试用已激活，",
        "hi": "✅ मुफ्त परीक्षण सक्रिय हुआ:",
        "es": "✅ Prueba gratis activada por",
        "fr": "✅ Essai gratuit activé pour",
        "ar": "✅ تم تفعيل التجربة المجانية لمدة",
        "pt": "✅ Teste grátis ativado por",
        "ru": "✅ Бесплатный триал активирован на",
        "ja": "✅ 無料トライアルが有効になりました:",
        "de": "✅ Kostenlose Testversion aktiviert für",
    },
    "trial_failed": {
        "en": "Trial failed:",
        "zh": "试用失败：",
        "hi": "परीक्षण विफल:",
        "es": "Prueba fallida:",
        "fr": "Échec de l'essai :",
        "ar": "فشلت التجربة:",
        "pt": "Falha no teste:",
        "ru": "Ошибка триала:",
        "ja": "トライアルに失敗:",
        "de": "Test fehlgeschlagen:",
    },
    "server_error": {
        "en": "Server error:",
        "zh": "服务器错误：",
        "hi": "सर्वर त्रुटि:",
        "es": "Error del servidor:",
        "fr": "Erreur du serveur :",
        "ar": "خطأ في الخادم:",
        "pt": "Erro do servidor:",
        "ru": "Ошибка сервера:",
        "ja": "サーバーエラー:",
        "de": "Serverfehler:",
    },
    "langs_hint": {
        "en": "Supported languages: en, zh, hi, es, fr, ar, pt, ru, ja, de",
        "zh": "支持的语言：en, zh, hi, es, fr, ar, pt, ru, ja, de",
        "hi": "समर्थित भाषाएँ: en, zh, hi, es, fr, ar, pt, ru, ja, de",
        "es": "Idiomas disponibles: en, zh, hi, es, fr, ar, pt, ru, ja, de",
        "fr": "Langues prises en charge : en, zh, hi, es, fr, ar, pt, ru, ja, de",
        "ar": "اللغات المدعومة: en, zh, hi, es, fr, ar, pt, ru, ja, de",
        "pt": "Idiomas suportados: en, zh, hi, es, fr, ar, pt, ru, ja, de",
        "ru": "Поддерживаемые языки: en, zh, hi, es, fr, ar, pt, ru, ja, de",
        "ja": "対応言語: en, zh, hi, es, fr, ar, pt, ru, ja, de",
        "de": "Unterstützte Sprachen: en, zh, hi, es, fr, ar, pt, ru, ja, de",
    },
}


def detect_lang() -> str:
    """--lang flag → VIBO_LANG env → system locale → en."""
    argv = sys.argv[1:]
    for i, a in enumerate(argv):
        if a == "--lang" and i + 1 < len(argv):
            return argv[i + 1].lower() if argv[i + 1].lower() in LANGS else "en"
    env = os.environ.get("VIBO_LANG", "").lower()
    if env in LANGS:
        return env
    # System locale: LANG/LC_ALL env vars first (no deprecation warnings).
    for var in ("LC_ALL", "LC_MESSAGES", "LANG"):
        raw = os.environ.get(var, "")
        code = raw.split(".")[0].split("_")[0].lower()
        if code in LANGS:
            return code
    return "en"


def strip_lang_args(argv: list[str]) -> list[str]:
    """Remove --lang <code> from argv so the rest works unchanged."""
    out, skip = [], False
    for i, a in enumerate(argv):
        if skip:
            skip = False
            continue
        if a == "--lang":
            skip = True
            continue
        out.append(a)
    return out


def t(key: str, lang: str) -> str:
    return T.get(key, {}).get(lang, T.get(key, {}).get("en", key))


def main() -> None:
    """Activator entry point."""
    lang = detect_lang()
    args = strip_lang_args(sys.argv[1:])

    if not args or args[0] in ("--help", "-h"):
        print(t("usage", lang))
        print(t("usage_key", lang))
        print(t("usage_email", lang))
        print(t("usage_lang", lang))
        print(t("langs_hint", lang))
        sys.exit(0 if args and args[0] in ("--help", "-h") else 1)

    if len(args) >= 2 and args[0] == "--email":
        email = args[1]
        result = trial_by_email(email, LICENSE_PATH)
        print(result["message"])
        sys.exit(0 if result["ok"] else 1)

    key = args[0]
    result = activate(key, LICENSE_PATH)
    if result["ok"]:
        print(t("activated", lang))
        print("🔑 VIBO-" + ("*" * 12))
        sys.exit(0)
    msg = (result.get("message") or "").lower()
    if "not found" in msg or "not_found" in msg:
        print(t("key_not_found", lang))
    else:
        print(f"{t('activation_failed', lang)} {result.get('message', '?')}")
    sys.exit(1)


def trial_by_email(email: str, license_path: Path) -> dict:
    """Get a trial key by email (works from any install: n8n, ClawHub, site)."""
    import json
    import urllib.error
    import urllib.request

    lang = detect_lang()
    # Same server override as license.py (local testing = VIBO_ACTIVATION_SERVER).
    server = os.environ.get("VIBO_ACTIVATION_SERVER", "https://wwwvibo.com")
    try:
        req = urllib.request.Request(
            f"{server}/trial",
            data=json.dumps({"email": email}).encode(),
            headers={"Content-Type": "application/json",
                     "User-Agent": "ViBoSkill/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.loads(r.read())
        if not d.get("ok"):
            return {"ok": False, "message": d.get("message", t("trial_failed", lang))}
        key = d["key"]
        res = activate(key, license_path)
        if res["ok"]:
            days = d.get("days", 2)
            return {"ok": True,
                    "message": f"{t('trial_activated', lang)} {days} days. Key: {key}"}
        return res
    except urllib.error.HTTPError as e:
        return {"ok": False, "message": f"{t('server_error', lang)} {e.code}"}
    except Exception as e:
        return {"ok": False, "message": f"{t('trial_failed', lang)} {e}"}


if __name__ == "__main__":
    main()
