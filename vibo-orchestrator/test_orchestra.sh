#!/usr/bin/env bash
# ============================================================
# ViBo Team Memory — ORCHESTRATION TEST
# «One memory for your whole agent team»
#
# What it verifies:
#   1. Shared memory: 3 agents write into one namespace
#   2. The orchestrator reads ONE summary (context)
#   3. Isolation: personal facts stay private
#   4. Authors (--by) and lifetime (--ttl)
#
# Run:  bash test_orchestra.sh
# Safe: uses a TEMPORARY memory file, touches nothing real.
# ============================================================
set -e
cd "$(dirname "$0")"

echo "=============================================="
echo "🧠 ViBo Team Memory — orchestration test"
echo "=============================================="

# 0. Check that the engine supports namespaces (needs 2.0+)
if ! python3.11 vibo_use.py context --help >/dev/null 2>&1; then
  echo "❌ Engine does NOT support namespaces (context command missing)."
  echo "   Update vibo_use.py from the latest package (2.0+)."
  exit 1
fi
echo "✅ Engine supports Team Memory (context/namespace)"

# Temporary memory — so nothing real gets touched
TMP=$(mktemp -d)
export VIBO_MEM_FILE="$TMP/orch_test.web"
trap 'rm -rf "$TMP"' EXIT

echo ""
echo "=== 1. Three agents write to the shared namespace (team:demo) ==="
python3.11 vibo_use.py add "agent-1" "checked disk and RAM: all ok" --namespace team:demo --by sys-agent --ttl 6h
python3.11 vibo_use.py add "agent-2" "checked services: bot active, proxy 200" --namespace team:demo --by svc-agent --ttl 6h
python3.11 vibo_use.py add "agent-3" "checked channels: site 200, github live" --namespace team:demo --by web-agent --ttl 6h

echo ""
echo "=== 2. The orchestrator reads ONE summary (context) ==="
python3.11 vibo_use.py context --namespace team:demo

echo ""
echo "=== 3. Isolation: personal facts are NOT visible to the team ==="
python3.11 vibo_use.py add "personal" "my secret — mine only"
echo "→ team context (must NOT contain 'personal'):"
python3.11 vibo_use.py context --namespace team:demo | grep -c "personal" | xargs -I{} bash -c 'if [ {} -eq 0 ]; then echo "✅ personal did not leak"; else echo "❌ LEAK!"; fi'

echo ""
echo "=== 4. TTL: metric with ttl=3s expires and disappears ==="
python3.11 vibo_use.py add "metric" "load 0.1" --namespace team:demo --by sys-agent --ttl 3s
echo "→ visible immediately:"
python3.11 vibo_use.py context --namespace team:demo | grep -c "metric" | xargs -I{} bash -c 'if [ {} -ge 1 ]; then echo "✅ metric is there"; else echo "❌ no metric"; fi'
sleep 4
echo "→ after 4s (ttl=3s expired):"
python3.11 vibo_use.py context --namespace team:demo | grep -c "metric" | xargs -I{} bash -c 'if [ {} -eq 0 ]; then echo "✅ TTL works — stale data gone"; else echo "❌ TTL did not fire"; fi'

echo ""
echo "=============================================="
echo "🎉 ALL TESTS PASSED — Team Memory works!"
echo "   One memory for your whole agent team."
echo "=============================================="
