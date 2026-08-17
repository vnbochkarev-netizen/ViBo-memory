#!/usr/bin/env python3
"""ViBo CLI — fast memory operations (for agents and users).

Usage:
    vibo_use.py add "label" "fact" [--tag xxx]
    vibo_use.py find "query" [--limit 5]
    vibo_use.py stats
    vibo_use.py link "label1" "label2" [--rel follows]

Every operation is logged to the usage log (savings measurement).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from vibo.core import Graph
from vibo.crypto import Crypto, SecurityLevel
from vibo.storage import WebFile

MEM_FILE = Path(os.environ.get("VIBO_MEM_FILE", "memory.web"))

VERSION = "2.0.1"
STATE_NODE_ID = "state_live"


def _load_user_password() -> str | None:
    """L3 user password: from env VIBO_USER_PASSWORD, else ~/.vibo/user.key."""
    env_pw = os.environ.get("VIBO_USER_PASSWORD", "").strip()
    if env_pw:
        return env_pw
    key_file = Path(os.environ.get("VIBO_HOME", str(Path.home() / ".vibo"))) / "user.key"
    if key_file.exists():
        return key_file.read_text(encoding="utf-8").strip()
    return None


USER_PASSWORD = _load_user_password()


def _load_agent_key() -> str:
    """Persistent random agent key for L2 encryption (generated once).

    Stored in ~/.vibo/agent.key (chmod 600) so L2 nodes stay decryptable
    across sessions without a hardcoded secret. Override via VIBO_AGENT_KEY.
    """
    import base64

    env_key = os.environ.get("VIBO_AGENT_KEY", "").strip()
    if env_key:
        return env_key
    key_dir = Path(os.environ.get("VIBO_HOME", str(Path.home() / ".vibo")))
    key_file = key_dir / "agent.key"
    if key_file.exists():
        return key_file.read_text(encoding="utf-8").strip()
    key = base64.urlsafe_b64encode(os.urandom(32)).decode()
    key_dir.mkdir(parents=True, exist_ok=True)
    key_file.write_text(key, encoding="utf-8")
    try:
        key_file.chmod(0o600)
    except OSError:
        pass
    return key


def _is_encrypted(content: str) -> bool:
    """Heuristic: valid base64 of >= 28 bytes (AES-GCM nonce+tag)."""
    import base64

    if len(content) < 38:
        return False
    try:
        return len(base64.b64decode(content, validate=True)) >= 28
    except Exception:
        return False


def _secret_hints(label: str, content: str) -> bool:
    """Detect secret-looking nodes: markers, keywords, or value patterns.

    Checks the FULL content (not just the first 200 chars) — secrets can be
    embedded deep inside a long diary/digest node.
    """
    import re

    if "enc:" in content:
        return True
    low = (label + " " + content).lower()
    keywords = ("password", "пароль", "passwd", "token", "токен", "api key",
                "api_key", "secret", "секрет", "oauth", "client_id",
                "client_secret", "ключ")
    if any(k in low for k in keywords):
        return True
    # value patterns (secret-looking strings embedded in free text)
    patterns = (
        r"sk-[A-Za-z0-9]{16,}",                              # OpenAI/Anthropic keys
        r"ghp_[A-Za-z0-9]{20,}",                             # GitHub PAT
        r"xkeysib-[A-Za-z0-9-]{10,}",                        # Brevo
        r"AKIA[0-9A-Z]{16}",                                 # AWS access key
        r"\d{8,10}:AA[A-Za-z0-9_-]{20,}",                    # Telegram bot token
        r"\d{8,}-[a-z0-9]+\.apps\.googleusercontent\.com",   # OAuth client id
    )
    return any(re.search(p, content) for p in patterns)


def _strip_enc(content: str) -> str:
    return content.replace("enc:", "")


def _auto_migrate_secrets(graph: Graph, crypto: Crypto) -> None:
    """Self-heal: encrypt plaintext secrets left from older versions.

    Idempotent — after migration the secrets are encrypted, so later loads
    skip them. Backs up memory.web before the first write.
    """
    changed = False
    for node in graph.nodes.values():
        if _is_encrypted(node.content):
            continue  # already encrypted
        if node.level in ("L2", "L3") or _secret_hints(node.label, node.content):
            plaintext = _strip_enc(node.content)
            if node.level == "L2":
                node.content = crypto.seal(SecurityLevel.L2_PRIVATE, plaintext)
            elif USER_PASSWORD is not None:
                node.content = crypto.seal(SecurityLevel.L3_SECRET, plaintext)
                node.level = "L3"
            else:
                # no user passphrase — at least encrypt with the agent key
                node.content = crypto.seal(SecurityLevel.L2_PRIVATE, plaintext)
                node.level = "L2"
            changed = True
    if changed:
        bak = MEM_FILE.with_name(f"{MEM_FILE.name}.bak-{time.strftime('%Y%m%d_%H%M%S')}")
        bak.write_bytes(MEM_FILE.read_bytes())
        WebFile(MEM_FILE).write(graph, crypto=crypto)


def load() -> tuple[Graph, Crypto]:
    agent_key = _load_agent_key()
    salt = WebFile(MEM_FILE).read_salt() if MEM_FILE.exists() else None
    crypto = Crypto(agent_key=agent_key, user_password=USER_PASSWORD, salt=salt)
    if MEM_FILE.exists():
        graph = WebFile(MEM_FILE).read()
        _auto_migrate_secrets(graph, crypto)
        return graph, crypto
    return Graph(), crypto


def save(graph: Graph, crypto: Crypto) -> None:
    WebFile(MEM_FILE).write(graph, crypto=crypto)


def _parse_ttl(s: str) -> float | None:
    """Parse lifetime: '1h'/'6h'/'1d'/'7d' or seconds. Empty → None."""
    if not s:
        return None
    s = s.strip().lower()
    units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    if s[-1] in units:
        try:
            return float(s[:-1]) * units[s[-1]]
        except ValueError:
            return None
    try:
        return float(s)
    except ValueError:
        return None


def _filter_namespace(graph: Graph, namespace: str) -> Graph:
    """Sub-graph with only the nodes of the given namespace (+ their edges).

    Namespace is stored as a tag `ns:<name>` (compatible with the compiled
    core — no MemoryNode field changes needed). `default` = no ns: tag.
    """
    g = Graph()
    for n in graph.nodes.values():
        if n.is_expired():
            continue
        has_ns = any(t.startswith("ns:") for t in n.tags)
        if namespace == "default" and not has_ns:
            g.nodes[n.id] = n
        elif f"ns:{namespace}" in n.tags:
            g.nodes[n.id] = n
    for e in graph.edges:
        if e.source in g.nodes and e.target in g.nodes:
            g.edges.append(e)
    return g


def _load_index():
    """Vector index (Phase 2+3): sidecar file next to the .web file."""
    from vibo.vector_index import VectorIndex

    return VectorIndex(MEM_FILE.with_suffix(MEM_FILE.suffix + ".vec"))


def _tier() -> str:
    """License tier from vibo_license.dat payload: 'trial' → 'free', else 'paid'."""
    try:
        import json
        from pathlib import Path
        p = Path(__file__).parent / "vibo_license.dat"
        if not p.exists():
            return "free"
        d = json.loads(p.read_text(encoding="utf-8"))
        t = (d.get("payload") or {}).get("type", "trial")
        return "free" if t == "trial" else "paid"
    except Exception:
        return "free"


FREE_LIMIT = 500  # free tier: up to 500 facts forever

# Orchestrator demo limits (enabled with VIBO_DEMO_MODE=1)
DEMO_FACT_LIMIT = int(os.environ.get("VIBO_DEMO_FACTS", "50"))
DEMO_NS_LIMIT = int(os.environ.get("VIBO_DEMO_NS", "2"))


def _demo_limits_blocked(graph, namespace: str) -> str | None:
    """Return an upgrade message if demo limits are exhausted, else None."""
    if os.environ.get("VIBO_DEMO_MODE") != "1":
        return None
    if namespace != "default":
        ns_set = {next((t[3:] for t in n.tags if t.startswith("ns:")), "default") for n in graph.nodes.values()}
        if namespace not in ns_set and len(ns_set) >= DEMO_NS_LIMIT:
            return (f"⛔ Demo limit reached ({DEMO_NS_LIMIT} team namespaces). "
                    f"Get your key: $5/mo → https://wwwvibo.com")
    if graph.stats()["nodes"] >= DEMO_FACT_LIMIT:
        return (f"⛔ Demo limit reached ({DEMO_FACT_LIMIT} facts). "
                f"Get your key: $5/mo → https://wwwvibo.com")
    return None


def _free_blocked(graph) -> bool:
    """True if free tier and the fact limit is exhausted."""
    if _tier() != "free":
        return False
    return graph.stats()["nodes"] >= FREE_LIMIT


def _free_upgrade_msg() -> str:
    return (f"⛔ Free limit reached ({FREE_LIMIT} facts). "
            f"Upgrade: $5/mo or $60 lifetime → https://wwwvibo.com")


def main() -> int:
    parser = argparse.ArgumentParser(description="ViBo memory")
    parser.add_argument("--trace", action="store_true", help="Emit JSON trace of operations (for debuggers)")
    sub = parser.add_subparsers(dest="cmd")

    pa = sub.add_parser("add", help="Add a fact")
    pa.add_argument("label")
    pa.add_argument("content")
    pa.add_argument("--tag", action="append", default=["fact"])
    pa.add_argument("--level", choices=["L1", "L2", "L3"], default="L1",
                    help="L1 public / L2 private (agent key) / L3 secret (user password)")
    pa.add_argument("--namespace", default="default", help="Team Memory: shared space for an agent team (team:x)")
    pa.add_argument("--by", default="", help="Author of the record (agent) — visible in context")
    pa.add_argument("--ttl", default="", help="Lifetime: 1h / 6h / 1d / 7d (for metrics)")
    pa.add_argument("--inbox", action="store_true", help="Important owner event (token/key/command) — shown in resume")

    pf = sub.add_parser("find", help="Find facts")
    pf.add_argument("query")
    pf.add_argument("--limit", type=int, default=5)
    pf.add_argument("--namespace", default="default", help="Search inside a namespace")

    pc = sub.add_parser("context", help="Team Memory: shared summary for the orchestrator")
    pc.add_argument("--namespace", default="default")
    pc.add_argument("--limit", type=int, default=1200, help="Max characters of the summary")

    ps = sub.add_parser("stats", help="Memory stats")

    pu = sub.add_parser("usage", help="Real token & money savings")

    pw = sub.add_parser("web", help="Web search: compress article / cache")
    pw.add_argument("--compress", metavar="FILE|URL", help="Compress article (file or URL)")
    pw.add_argument("--query", default="", help="Query for compression")
    pw.add_argument("--cache", action="store_true", help="Show search cache")

    pl = sub.add_parser("link", help="Link facts")
    pl.add_argument("from_label")
    pl.add_argument("to_label")
    pl.add_argument("--rel", default="follows")

    pr = sub.add_parser("reveal", help="Show an L3 secret (asks for the password)")
    pr.add_argument("label")

    pst = sub.add_parser("setup", help="Set your L3 secret password (once)")
    pst.add_argument("password", nargs="?", default=None,
                     help="Password (positional)")
    pst.add_argument("--password", dest="password_opt", default=None,
                     help="Password (flag form)")

    pfgt = sub.add_parser("forget", help="Delete a fact from memory")
    pfgt.add_argument("label")

    pwp = sub.add_parser("wipe", help="Delete ALL memory (irreversible)")
    pwp.add_argument("--yes", action="store_true", help="Confirm deletion")

    pd = sub.add_parser("dialog", help="Thread Memory (dialog)")
    pd.add_argument("action", choices=["add", "compress", "ask", "context", "mode"])
    pd.add_argument("text", nargs="?", default="", help="Message or question")
    pd.add_argument("--role", default="user", help="Role: user/assistant")
    pd.add_argument("--topic", default="", help="Topic")
    pd.add_argument("--file", default="thread.web", help="Dialog memory file")
    pd.add_argument("--mode", choices=["full", "summary"], default=None,
                    help="full — whole history (details restorable), summary — only essence")

    pc = sub.add_parser("change", help="Switch thread memory mode (full|summary)")
    pc.add_argument("mode", nargs="?", default="", help="full or summary")
    pc.add_argument("--file", default="thread.web", help="Dialog memory file")

    pa = sub.add_parser("archive", help="ViBo Archive: pack/search/list/info/unpack documents")
    pa_sub = pa.add_subparsers(dest="cmd2")
    pa_p = pa_sub.add_parser("pack", help="Pack files/folder into .vibo")
    pa_p.add_argument("inputs", nargs="+")
    pa_p.add_argument("-o", "--output", default="archive.vibo")
    pa_p.add_argument("--light", action="store_true")
    pa_s = pa_sub.add_parser("search", help="Search by meaning in archive")
    pa_s.add_argument("archive")
    pa_s.add_argument("query")
    pa_s.add_argument("--limit", type=int, default=3)
    pa_l = pa_sub.add_parser("list", help="List documents in archive")
    pa_l.add_argument("archive")
    pa_i = pa_sub.add_parser("info", help="Archive statistics")
    pa_i.add_argument("archive")
    pa_u = pa_sub.add_parser("unpack", help="Unpack .vibo back to files")
    pa_u.add_argument("archive")
    pa_u.add_argument("-o", "--output", default="unpacked")

    pst = sub.add_parser("save-state", help="Write a snapshot of where you stopped")
    pst.add_argument("text", nargs="?", default="", help="One-line summary (if no fields given)")
    pst.add_argument("--task", default="", help="What you are doing")
    pst.add_argument("--done", default="", help="What is already done")
    pst.add_argument("--next", default="", help="Next step")
    pst.add_argument("--waiting", default="", help="What awaits a human decision")
    pst.add_argument("--files", default="", help="Touched files/paths")

    prs = sub.add_parser("resume", help="Return the snapshot (continue where you stopped)")
    prs.add_argument("--json", action="store_true", help="Raw JSON for pipelines")

    pver = sub.add_parser("version", help="ViBo version")

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return 1

    if args.cmd == "version":
        print(f"ViBo {VERSION} \u2014 Live Handoff (resume/save-state)")
        return 0

    graph, crypto = load()

    if args.cmd == "setup":
        pw = getattr(args, "password", None)
        if not pw:
            pw = getattr(args, "password_opt", None)
        if pw is None:
            import getpass
            try:
                pw = getpass.getpass("Secret password for L3: ")
                pw2 = getpass.getpass("Repeat password: ")
                if pw != pw2:
                    print("❌ Passwords don't match")
                    return 1
            except (EOFError, OSError):
                pw = (sys.stdin.readline() or "").strip()
        if not pw:
            print("❌ Empty password")
            return 1
        key_dir = Path(os.environ.get("VIBO_HOME", str(Path.home() / ".vibo")))
        key_dir.mkdir(parents=True, exist_ok=True)
        (key_dir / "user.key").write_text(pw, encoding="utf-8")
        try:
            (key_dir / "user.key").chmod(0o600)
        except OSError:
            pass
        print("✅ Secret password saved. Now: vibo add 'label' 'value' --level L3")
        return 0

    if args.cmd == "forget":
        node = next((n for n in graph.nodes.values() if n.label.lower() == args.label.lower()), None)
        if node is None:
            print(f"❌ Not found: {args.label}")
            return 1
        graph.remove_node(node.id)
        save(graph, crypto)
        print(f"🗑️ Deleted: {node.label}")
        return 0

    if args.cmd == "wipe":
        if not getattr(args, "yes", False):
            print("⚠️ This deletes ALL memory (memory.web + archive + index).")
            print("   To confirm: vibo wipe --yes")
            return 1
        for p in (MEM_FILE,
                  MEM_FILE.with_name(MEM_FILE.stem + "_archive.web"),
                  MEM_FILE.with_suffix(MEM_FILE.suffix + ".vec")):
            if p.exists():
                p.unlink()
        print("🗑️ All memory wiped.")
        return 0

    if args.cmd == "reveal":
        node = next((n for n in graph.nodes.values() if n.label.lower() == args.label.lower()), None)
        if node is None:
            print(f"❌ Not found: {args.label}")
            return 1
        if node.level != "L3":
            print(f"[{node.level}] {node.label}: {node.content}")
            return 0
        pw = USER_PASSWORD
        if not pw:
            import getpass
            try:
                pw = getpass.getpass("Secret password: ")
            except (EOFError, OSError):
                pw = (sys.stdin.readline() or "").strip()
        if not pw:
            print("❌ Password required — run: vibo setup <password>  (or set VIBO_USER_PASSWORD)")
            return 1
        salt = WebFile(MEM_FILE).read_salt() if MEM_FILE.exists() else None
        c2 = Crypto(agent_key=_load_agent_key(), user_password=pw, salt=salt)
        try:
            print(f"[L3] {node.label}: {c2.open(node.content, SecurityLevel.L3_SECRET)}")
        except Exception:
            print("🔒 Wrong password or undecryptable")
            return 1
        return 0

    if args.cmd == "add":
        # Dedup ONLY by exact normalized label+content match.
        # Semantic search NOT used here — too aggressive
        # on small bases and blocks unique records.
        norm_label = " ".join(args.label.lower().split())
        norm_content = " ".join(args.content.lower().split())
        exact_dup = any(
            " ".join(n.label.lower().split()) == norm_label
            and " ".join(n.content.lower().split()) == norm_content
            for n in graph.nodes.values()
        )
        if exact_dup:
            print(f"Already exists: {args.label} (exact duplicate, skipped)")
            return 0
        node_id = f"n{int(time.time()*1000)}"
        if _free_blocked(graph):
            print(_free_upgrade_msg())
            return 1
        demo_msg = _demo_limits_blocked(graph, getattr(args, "namespace", "default"))
        if demo_msg:
            print(demo_msg)
            return 1
        level = getattr(args, "level", "L1")
        content = args.content
        if level == "L2":
            content = crypto.seal(SecurityLevel.L2_PRIVATE, args.content)
        elif level == "L3":
            if USER_PASSWORD is None:
                print("🔒 L3 requires VIBO_USER_PASSWORD (user passphrase).")
                print("   Run: export VIBO_USER_PASSWORD=...  then retry.")
                return 1
            content = crypto.seal(SecurityLevel.L3_SECRET, args.content)
        tags = list(args.tag)
        if getattr(args, "by", ""):
            tags.append(f"by:{args.by}")
        if getattr(args, "inbox", False):
            tags.append("inbox")
        namespace = getattr(args, "namespace", "default")
        if namespace != "default":
            tags.append(f"ns:{namespace}")
        ttl = _parse_ttl(getattr(args, "ttl", ""))
        graph.add_node(args.label[:60], content, level=level, tags=tags, node_id=node_id, ttl=ttl)
        # Link to the "user" anchor — only for personal (default) namespace
        if namespace == "default":
            anchor = next((n for n in graph.nodes.values() if n.id == "user1"), None)
            if anchor:
                graph.add_edge(anchor.id, node_id, "about", weight=0.6)
        save(graph, crypto)
        # Update the vector index (embeds only the new node)
        try:
            idx = _load_index()
            idx.ensure_nodes(graph, node_ids=[node_id])
            idx.save()
        except Exception:
            pass
        print(f"✅ Added: {args.label} ({graph.stats()['nodes']} nodes)")

    elif args.cmd == "find":
        from vibo.navigator import ViBoNavigator

        idx = _load_index()
        ns = getattr(args, "namespace", "default")
        nav_graph = graph if ns == "default" else _filter_namespace(graph, ns)
        nav = ViBoNavigator(nav_graph, crypto, max_context_chars=2000, index=idx)
        res, usage = nav.navigate_with_usage(args.query, model="deepseek")
        idx.save()

        # TRACE: JSON output of the operation (for debuggers, Agent-Devtools)
        if getattr(args, "trace", False):
            import json as _tj
            frags = [{"label": n.label[:60], "chars": len(n.content), "level": str(getattr(n, "level", "L1"))} for n in (res.nodes if hasattr(res, "nodes") else [])[:5]]
            print(_tj.dumps({"op": "memory_search", "query": args.query,
                             "fragments": frags,
                             "tokens_before": usage.get("total_tokens", 0),
                             "tokens_after": usage.get("comp_tokens", 0),
                             "saved_tokens": usage.get("saved_tokens", 0),
                             "saved_pct": usage.get("saved_pct", 0)}, ensure_ascii=False))

        # Archive is part of memory: savings vs ALL memory (desk + drawer)
        archive_chars = 0
        arch_path = MEM_FILE.with_name(MEM_FILE.stem + "_archive.web")
        if arch_path.exists():
            try:
                arch = WebFile(arch_path).read()
                archive_chars = sum(len(n.content) + len(n.label) + 2 for n in arch.nodes.values())
            except Exception:
                archive_chars = 0

        if archive_chars and usage.get("total_tokens"):
            usage = dict(usage)
            archive_tokens = archive_chars // 4
            total_tokens = usage["total_tokens"] + archive_tokens
            saved_tokens = max(0, total_tokens - usage.get("context_tokens", 0))
            usage["total_tokens"] = total_tokens
            usage["saved_tokens"] = saved_tokens
            usage["saved_pct"] = (saved_tokens / total_tokens * 100) if total_tokens else 0
            usage["saved_usd"] = saved_tokens / 1_000_000 * 0.14

        if not res.nodes:
            # Adaptive mode: empty context = small memory, nothing to save
            s = graph.stats()
            print(f"🤷 Memory is small ({s['nodes']} facts) — ViBo stays silent, no savings.")
            print("   Save more facts — savings grow with memory.")
            return 0
        for n in res.nodes[: args.limit]:
            level = str(n.level)
            if level == "L3" or "enc:" in n.content:
                content = "🔒 [secret — available only to the user]"
            elif level == "L2":
                try:
                    content = crypto.open(n.content, SecurityLevel.L2_PRIVATE)
                except Exception:
                    content = "🔒 [encrypted]"
            else:
                content = n.content
            print(f"• [{level}] {n.label}: {content[:80]}")
        print(f"💾 Savings: {usage['saved_tokens']} tok ({usage['saved_pct']:.0f}%) · ${usage['saved_usd']:.5f}")
        if archive_chars:
            print(f"   (all memory: desk {usage['total_tokens'] - archive_chars // 4} + archive {archive_chars // 4} tok.)")

    elif args.cmd == "context":
        ns = args.namespace
        nodes = []
        for n in graph.nodes.values():
            if n.is_expired():
                continue
            has_ns = any(t.startswith("ns:") for t in n.tags)
            if ns == "default" and not has_ns:
                nodes.append(n)
            elif f"ns:{ns}" in n.tags:
                nodes.append(n)
        if not nodes:
            print(f"🤷 Namespace «{ns}» is empty")
            return 0
        nodes.sort(key=lambda n: n.updated_at, reverse=True)
        lines = []
        total = 0
        for n in nodes:
            content = n.content
            level = str(n.level)
            if level == "L3" or "enc:" in content:
                try:
                    opened = crypto.open_agent_only(n.content, n.level)
                    content = opened if opened is not None else "🔒 [secret — owner only]"
                except Exception:
                    content = "🔒 [encrypted]"
            by = next((t[3:] for t in n.tags if t.startswith("by:")), "")
            prefix = f"[{by}] " if by else ""
            entry = f"• {prefix}{n.label}: {content}"
            if total + len(entry) > args.limit:
                break
            lines.append(entry)
            total += len(entry)
        print(f"# ViBo shared context «{ns}»: {len(nodes)} facts, shown {len(lines)}")
        print("\n".join(lines))

    elif args.cmd == "web":
        from vibo_web import compress_article, WebCache

        if args.cache:
            cache = WebCache()
            if not cache.data:
                print("Search cache is empty 🤷")
            else:
                print(f"Search cache ({len(cache.data)}):")
                for q, res in list(cache.data.items())[:10]:
                    print(f"  «{q}» → {res.get('tokens', '?')} tokens")
            return 0

        if not args.compress:
            print("Usage: vibo web --compress FILE [--query QUERY]")
            return 0

        # Compress file (or URL)
        src = args.compress
        if src.startswith("http"):
            import urllib.request

            try:
                req = urllib.request.Request(src, headers={
                    "User-Agent": "Mozilla/5.0 (ViBo Skill; +https://wwwvibo.com)",
                    "Accept": "text/html,application/xhtml+xml",
                })
                with urllib.request.urlopen(req, timeout=15) as resp:
                    text = resp.read().decode(errors="ignore")
            except Exception as e:
                print(f"Load error: {e}")
                return 1
        else:
            text = Path(src).read_text(errors="ignore")

        comp, stats = compress_article(text, args.query or src)
        print(f"📄 Article: {src}")
        print(f"   Original: {stats['orig_tokens']} tokens")
        print(f"   Compressed: {stats['comp_tokens']} tokens")
        print(f"   💾 Savings: {stats['saved_pct']}% "
              f"({stats['saved_tokens']} tok · ${stats['saved_tokens']/1e6*0.14:.4f} DeepSeek)")
        print(f"\n{comp[:600]}...")

    elif args.cmd == "stats":
        s = graph.stats()
        tier = _tier()
        if tier == "free":
            print(f"Nodes: {s['nodes']}/{FREE_LIMIT} (FREE), edges: {s['edges']}")
            print(f"   Free forever: {FREE_LIMIT} facts. Upgrade: $5/mo or $60 → https://wwwvibo.com")
        else:
            print(f"Nodes: {s['nodes']} (PAID), edges: {s['edges']}")
        for n in sorted(graph.nodes.values(), key=lambda x: x.label)[:10]:
            print(f"  {n.label[:50]}")

    elif args.cmd == "usage":
        from vibo.analytics import UsageRecorder
        from datetime import datetime

        rec = UsageRecorder()
        s = rec.summary(model="deepseek")
        log_path = rec.path  # same file the skill itself uses

        # TODAY measurements (real numbers)
        day_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        today_saved = 0
        today_ops = 0
        try:
            log = Path(log_path)
            if log.exists():
                for line in log.read_text().splitlines():
                    if not line.strip():
                        continue
                    d = json.loads(line)
                    ts = d.get("ts", 0)
                    if isinstance(ts, str):
                        try:
                            ts = float(ts)
                        except Exception:
                            continue
                    if ts >= day_start:
                        today_ops += 1
                        today_saved += d.get("saved_tokens", 0)
        except Exception:
            pass

        print("📊 ViBo: your real savings")
        print("=" * 45)
        print(f"📈 Today: {today_ops} ops")
        print(f"💾 Today: {today_saved:,} tokens saved")
        print(f"💰 Today: ${today_saved / 1_000_000 * 0.14:.4f} (DeepSeek)")
        print("-" * 45)
        if s["records"] == 0:
            print("No measurements yet. Do some searches and web compressions —")
            print("savings will appear here.")
        else:
            print(f"📈 All time: {s['records']} ops")
            print(f"💾 All time: {s['saved_tokens']:,} tokens")
            print(f"💰 All time: ${s['saved_usd']:.4f}")
            print("=" * 45)
            print("Without ViBo you'd pay for ALL memory and FULL articles.")
            print("With ViBo: only relevant facts + compressed articles.")
            print("")
            print("If 'Today: 0' — ViBo not used yet today.")
            print("Every search and compression adds real numbers here.")

    elif args.cmd == "archive":
        import sys as _s
        _s.path.insert(0, str(Path(__file__).parent))
        from vibo_archive import pack, search, list_docs, info, unpack
        c2 = getattr(args, "cmd2", None)
        if c2 == "pack":
            pack(args.inputs, args.output, light=getattr(args, "light", False))
        elif c2 == "search":
            search(args.query, args.archive, args.limit)
            if getattr(args, "trace", False):
                print('{"op": "archive_search", "query": "%s", "archive": "%s"}' % (args.query, args.archive))
        elif c2 == "list":
            list_docs(args.archive)
        elif c2 == "info":
            info(args.archive)
        elif c2 == "unpack":
            unpack(args.archive, args.output)
        else:
            print("vibo archive: pack | search | list | info | unpack")

    elif args.cmd == "change":
        # Simple mode switch: vibo change full|summary
        from vibo.dialog import DialogMemory

        dm = DialogMemory(path=args.file if hasattr(args, "file") and args.file else "thread.web", crypto=crypto)
        new_mode = args.mode.strip().lower()
        if not new_mode:
            print(f"Current mode: {dm.mode}")
            print("Switch: vibo change full | vibo change summary")
            return 0
        if new_mode not in ("full", "summary"):
            print("Usage: vibo change full|summary")
            return 1
        saved = dm.set_mode(new_mode)
        print(f"✅ Mode changed: {saved}")
        print("   full    — keeps ALL history (event chain restorable)")
        print("   summary — keeps only essence (max savings)")
        return 0

    elif args.cmd == "dialog":
        from vibo.dialog import DialogMemory

        dm = DialogMemory(path=args.file, crypto=crypto, mode=args.mode)

        if args.action == "mode":
            # Mode switch: vibo dialog mode full|summary
            new_mode = args.text.strip().lower()
            if new_mode not in ("full", "summary"):
                print("Usage: vibo dialog mode full|summary")
                print("  full    — all history, details restorable")
                print("  summary — only essence (max savings)")
                print(f"Now: {dm.mode}")
                return 1
            saved = dm.set_mode(new_mode)
            print(f"✅ Mode: {saved}")
            print("   full    — keeps ALL history (event chain restorable)")
            print("   summary — keeps only essence (max savings)")
            return 0

        if args.action == "add":
            if not args.text:
                print("Usage: vibo dialog add \"message\" [--role user] [--topic topic]")
                return 0
            res = dm.add(args.role, args.text, args.topic)
            print(f"💾 Saved to {args.file} (node: {res['nodes']})")

        elif args.action == "compress":
            res = dm.compress()
            if res["ok"]:
                print(f"📦 Compressed messages: {res.get('compressed', 0)}")
                if "orig_tokens" in res and "summary_tokens" in res:
                    print(f"   Before: {res['orig_tokens']} tok | After: {res['summary_tokens']} tok")
                    print(f"   💾 Savings: {res.get('saved_pct', 0)}% ({res.get('saved_tokens', 0)} tokens)")
                else:
                    print(f"   {res.get('message', 'Nothing to compress yet.')}")
            else:
                print(res.get("message", "Error"))

        elif args.action == "ask":
            if not args.text:
                print("Usage: vibo dialog ask \"what was 3 days ago?\"")
                return 0
            res = dm.ask(args.text)
            if not res:
                print("🤷 Nothing found in dialog history")
            else:
                print(f"🔍 Found ({len(res)}):")
                for r in res:
                    print(f"  • {r['content'][:120]}")

        elif args.action == "context":
            ctx = dm.compose()
            if not ctx:
                print("Empty — record a dialog first (vibo dialog add)")
            else:
                print(ctx)

    elif args.cmd == "link":
        a = next((n for n in graph.nodes.values() if n.label == args.from_label), None)
        b = next((n for n in graph.nodes.values() if n.label == args.to_label), None)
        if not a or not b:
            print(f"Nodes not found: {args.from_label}={'yes' if a else 'no'}, {args.to_label}={'yes' if b else 'no'}")
            return 1
        graph.add_edge(a.id, b.id, args.rel, weight=0.8)
        save(graph, crypto)
        print(f"🔗 Linked: {a.label} —{args.rel}→ {b.label}»")

    elif args.cmd == "save-state":
        payload = {
            "task": args.task or "",
            "done": args.done or "",
            "next": args.next or "",
            "waiting": args.waiting or "",
            "files": args.files or "",
        }
        if args.text and not any(payload.values()):
            payload["task"] = args.text
        if not any(payload.values()):
            print("Nothing to write: vibo save-state \"summary\" [--task --done --next --waiting --files]")
            return 1
        content = json.dumps(payload, ensure_ascii=False)
        node = graph.nodes.get(STATE_NODE_ID)
        if node:
            node.content = content
            node.updated_at = time.time()
            node.tags = list(dict.fromkeys(list(node.tags) + ["state", "live"]))
        else:
            graph.add_node("Snapshot", content, tags=["state", "live"], node_id=STATE_NODE_ID)
            anchor = next((n for n in graph.nodes.values() if n.id == "user1"), None)
            if anchor:
                graph.add_edge(anchor.id, STATE_NODE_ID, "about", weight=0.6)
        save(graph, crypto)
        print("\U0001f7e2 Snapshot updated:")
        for k in ("task", "done", "next", "waiting", "files"):
            if payload[k]:
                print(f"   {k}: {payload[k][:90]}")
        print("   (agent on start: vibo resume)")

    elif args.cmd == "resume":
        node = graph.nodes.get(STATE_NODE_ID)
        if not node:
            if args.json:
                print(json.dumps({}, ensure_ascii=False))
            else:
                print("\U0001f937 No snapshot yet \u2014 start with: vibo save-state \"what you are doing\"")
            return 0
        try:
            p = json.loads(node.content)
        except Exception:
            p = {"task": node.content}
        if args.json:
            print(json.dumps(p, ensure_ascii=False))
            return 0
        print("\U0001f7e2 ViBo snapshot (continue from here):")
        if p.get("task"):
            print(f"   \U0001f4cc Task: {p['task']}")
        if p.get("done"):
            print(f"   \u2705 Done: {p['done']}")
        if p.get("next"):
            print(f"   \u23ed\ufe0f Next: {p['next']}")
        if p.get("waiting"):
            print(f"   \u23f3 Waiting: {p['waiting']}")
        if p.get("files"):
            print(f"   \U0001f4c1 Files: {p['files']}")
        ts = getattr(node, "updated_at", None)
        if ts:
            from datetime import datetime
            print(f"   \U0001f550 Updated: {datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')}")

        # 📥 Important owner events (inbox) — last 5, so nothing is lost after /new
        inbox_nodes = [n for n in graph.nodes.values() if "inbox" in n.tags and not n.is_expired()]
        if inbox_nodes:
            inbox_nodes.sort(key=lambda n: n.updated_at, reverse=True)
            from datetime import datetime as _dt
            print("\n\U0001f4e5 Important events (inbox):")
            for n in inbox_nodes[:5]:
                ts = _dt.fromtimestamp(n.updated_at).strftime("%d.%m %H:%M")
                print(f"   • [{ts}] {n.label}: {n.content[:110]}")

        # 📋 Auto-journal — last 3 session actions (written automatically)
        journal_nodes = [n for n in graph.nodes.values() if "journal" in n.tags and any(t == "by:auto-journal" for t in n.tags)]
        if journal_nodes:
            journal_nodes.sort(key=lambda n: n.updated_at, reverse=True)
            print("\n\U0001f4cb Auto-journal (recent actions):")
            for n in journal_nodes[:3]:
                print(f"   • {n.content[:120]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
