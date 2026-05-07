#!/usr/bin/env bash
set -e

# Всегда запускаемся из директории скрипта
cd "$(dirname "$0")"

# ── Цвета ────────────────────────────────────────────────────────────────────
PURPLE='\033[0;35m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# ── Режим: ./run.sh test — запустить тесты ───────────────────────────────────
if [ "${1}" = "test" ]; then
    echo -e "${PURPLE}◆ Running tests...${NC}"
    if [ -d ".venv" ]; then
        .venv/bin/pip install pytest --quiet 2>/dev/null
        .venv/bin/pytest tests/ -v
    else
        python3 -m pip install pytest --quiet
        python3 -m pytest tests/ -v
    fi
    exit 0
fi

echo -e "${PURPLE}"
echo "  ◆ Job Fit & Salary Estimator"
echo "  AI-powered CV analysis pipeline"
echo -e "${NC}"

# ── Проверка .env ─────────────────────────────────────────────────────────────
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠  .env not found — copying from .env.example${NC}"
    cp .env.example .env
    echo -e "${RED}   → Open .env and set your ANTHROPIC_API_KEY, then re-run this script${NC}"
    exit 1
fi

if grep -q "your-key-here" .env 2>/dev/null; then
    echo -e "${YELLOW}⚠  ANTHROPIC_API_KEY not set in .env — you can enter it in the UI sidebar${NC}"
fi

API_KEY_VALUE=$(grep "ANTHROPIC_API_KEY" .env 2>/dev/null | cut -d'=' -f2)
if [ -z "$API_KEY_VALUE" ] || echo "$API_KEY_VALUE" | grep -q "your-key-here"; then
    echo -e "${YELLOW}⚠  No API key in .env — enter it in the UI sidebar after launch${NC}"
fi

# ── Виртуальное окружение ─────────────────────────────────────────────────────
VENV_DIR=".venv"

if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}⟳  Creating virtual environment...${NC}"
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

# ── Проверка зависимостей ─────────────────────────────────────────────────────
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}⟳  Installing dependencies...${NC}"
    pip install -r requirements.txt --quiet
fi

# ── Cleanup при выходе ────────────────────────────────────────────────────────
cleanup() {
    echo -e "\n${YELLOW}⏹  Stopping services...${NC}"
    kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
    echo -e "${GREEN}✓  Done${NC}"
}
trap cleanup EXIT INT TERM

# ── Запуск backend ────────────────────────────────────────────────────────────
echo -e "${GREEN}▶  Starting backend  →  http://localhost:8000${NC}"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload \
    --log-level warning &
BACKEND_PID=$!

# Ждём пока backend поднимется
echo -n "   Waiting for API"
for i in $(seq 1 15); do
    sleep 1
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e " ${GREEN}✓${NC}"
        break
    fi
    echo -n "."
    if [ "$i" -eq 15 ]; then
        echo -e " ${RED}✗ Backend failed to start${NC}"
        exit 1
    fi
done

# ── Запуск frontend ───────────────────────────────────────────────────────────
echo -e "${GREEN}▶  Starting frontend →  http://localhost:8501${NC}"
streamlit run frontend/streamlit_app.py \
    --server.port 8501 \
    --server.headless true \
    --browser.gatherUsageStats false &
FRONTEND_PID=$!

echo ""
echo -e "${PURPLE}  ✓ App is running!${NC}"
echo -e "  Frontend  →  ${GREEN}http://localhost:8501${NC}"
echo -e "  API docs  →  ${GREEN}http://localhost:8000/docs${NC}"
echo -e "  Press ${YELLOW}Ctrl+C${NC} to stop"
echo -e "  Run tests →  ${YELLOW}./run.sh test${NC}"
echo ""

# Держим скрипт живым
wait
