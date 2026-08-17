"""License check on every skill run.

The skill (SKILL.md) calls this script first:
    python3 check_license.py [--lang <code>]

Logic:
1. If vibo_license.dat exists (activated license) — verify it.
2. Otherwise — tell the user to activate (activate.py).

Languages (--lang or VIBO_LANG or system locale): en, zh, hi, es, fr, ar, pt, ru, ja, de
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from license import check  # noqa: E402

LICENSE_DAT = Path(__file__).parent / "vibo_license.dat"

LANGS = ["en", "zh", "hi", "es", "fr", "ar", "pt", "ru", "ja", "de"]

T = {
    "not_activated": {
        "en": "🔒 ViBo: License is not activated.",
        "zh": "🔒 ViBo：许可证尚未激活。",
        "hi": "🔒 ViBo: लाइसेंस सक्रिय नहीं है।",
        "es": "🔒 ViBo: la licencia no está activada.",
        "fr": "🔒 ViBo : la licence n'est pas activée.",
        "ar": "🔒 ViBo: الترخيص غير مفعّل.",
        "pt": "🔒 ViBo: a licença não está ativada.",
        "ru": "🔒 ViBo: Лицензия не активирована.",
        "ja": "🔒 ViBo: ライセンスが有効になっていません。",
        "de": "🔒 ViBo: Lizenz ist nicht aktiviert.",
    },
    "activate_now": {
        "en": "   Activate: python3 activate.py VIBO-XXXX-XXXX-XXXX-XXXX",
        "zh": "   激活：python3 activate.py VIBO-XXXX-XXXX-XXXX-XXXX",
        "hi": "   सक्रिय करें: python3 activate.py VIBO-XXXX-XXXX-XXXX-XXXX",
        "es": "   Activar: python3 activate.py VIBO-XXXX-XXXX-XXXX-XXXX",
        "fr": "   Activer : python3 activate.py VIBO-XXXX-XXXX-XXXX-XXXX",
        "ar": "   التفعيل: python3 activate.py VIBO-XXXX-XXXX-XXXX-XXXX",
        "pt": "   Ativar: python3 activate.py VIBO-XXXX-XXXX-XXXX-XXXX",
        "ru": "   Активация: python3 activate.py VIBO-XXXX-XXXX-XXXX-XXXX",
        "ja": "   アクティベート: python3 activate.py VIBO-XXXX-XXXX-XXXX-XXXX",
        "de": "   Aktivieren: python3 activate.py VIBO-XXXX-XXXX-XXXX-XXXX",
    },
    "trial_now": {
        "en": "   Or trial: python3 activate.py --email you@example.com  (free 2 days)",
        "zh": "   或试用：python3 activate.py --email you@example.com  （免费2天）",
        "hi": "   या परीक्षण: python3 activate.py --email you@example.com  (मुफ्त 2 दिन)",
        "es": "   O prueba: python3 activate.py --email you@example.com  (gratis 2 días)",
        "fr": "   Ou essai : python3 activate.py --email you@example.com  (2 jours gratuits)",
        "ar": "   أو تجربة: python3 activate.py --email you@example.com  (يومان مجانًا)",
        "pt": "   Ou teste: python3 activate.py --email you@example.com  (grátis 2 dias)",
        "ru": "   Или триал: python3 activate.py --email you@example.com  (бесплатно 2 дня)",
        "ja": "   またはトライアル: python3 activate.py --email you@example.com  (2日間無料)",
        "de": "   Oder Test: python3 activate.py --email you@example.com  (2 Tage kostenlos)",
    },
    "buy_now": {
        "en": "   Buy: https://wwwvibo.com",
        "zh": "   购买：https://wwwvibo.com",
        "hi": "   खरीदें: https://wwwvibo.com",
        "es": "   Comprar: https://wwwvibo.com",
        "fr": "   Acheter : https://wwwvibo.com",
        "ar": "   الشراء: https://wwwvibo.com",
        "pt": "   Comprar: https://wwwvibo.com",
        "ru": "   Купить: https://wwwvibo.com",
        "ja": "   購入: https://wwwvibo.com",
        "de": "   Kaufen: https://wwwvibo.com",
    },
    "valid": {
        "en": "🔓 ViBo: License is valid.",
        "zh": "🔓 ViBo：许可证有效。",
        "hi": "🔓 ViBo: लाइसेंस मान्य है।",
        "es": "🔓 ViBo: la licencia es válida.",
        "fr": "🔓 ViBo : la licence est valide.",
        "ar": "🔓 ViBo: الترخيص ساري.",
        "pt": "🔓 ViBo: a licença é válida.",
        "ru": "🔓 ViBo: Лицензия действительна.",
        "ja": "🔓 ViBo: ライセンスは有効です。",
        "de": "🔓 ViBo: Lizenz ist gültig.",
    },
}


def detect_lang() -> str:
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


def t(key: str, lang: str) -> str:
    return T.get(key, {}).get(lang, T.get(key, {}).get("en", key))


def main() -> None:
    """License check entry point."""
    lang = detect_lang()
    result = check(LICENSE_DAT)
    if not result["ok"]:
        print(t("not_activated", lang))
        print(t("activate_now", lang))
        print(t("trial_now", lang))
        print(t("buy_now", lang))
        sys.exit(1)
    print(t("valid", lang))


if __name__ == "__main__":
    main()
