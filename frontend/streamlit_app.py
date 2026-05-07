import hashlib
import json as _json

import httpx
import streamlit as st

# ── Конфигурация ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Job Fit & Salary Estimator",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_URL = "http://localhost:8000"

# ── Стили ────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
/* Sidebar accent border */
[data-testid="stSidebar"] {
    border-right: 1px solid #2D3748;
}

/* Заголовок */
.hero-title {
    font-size: 2.4rem;
    font-weight: 800;
    background: linear-gradient(135deg, #6C63FF, #00D4AA);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.2rem;
}
.hero-subtitle {
    color: #718096;
    font-size: 1rem;
    margin-bottom: 2rem;
}

/* KPI карточки */
.kpi-card {
    background: #161B27;
    border: 1px solid #2D3748;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    text-align: center;
}
.kpi-label {
    color: #718096;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.4rem;
}
.kpi-value {
    font-size: 2rem;
    font-weight: 700;
    color: #FAFAFA;
    line-height: 1;
}
.kpi-value.accent  { color: #6C63FF; }
.kpi-value.success { color: #00D4AA; }
.kpi-value.warning { color: #FFB347; }

/* Skill теги */
.tag {
    display: inline-block;
    background: #1E2535;
    border: 1px solid #6C63FF44;
    color: #A78BFA;
    border-radius: 6px;
    padding: 0.2rem 0.6rem;
    margin: 0.2rem;
    font-size: 0.8rem;
    font-family: monospace;
}
.tag-soft {
    border-color: #00D4AA44;
    color: #00D4AA;
}

/* Карточки рекомендаций */
.rec-card {
    background: #161B27;
    border: 1px solid #2D3748;
    border-left: 4px solid #6C63FF;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
    position: relative;
}
.rec-card.high   { border-left-color: #00D4AA; }
.rec-card.medium { border-left-color: #FFB347; }
.rec-card.low    { border-left-color: #718096; }

.rec-number {
    position: absolute;
    top: 0.8rem;
    right: 1rem;
    font-size: 1.8rem;
    font-weight: 900;
    opacity: 0.08;
    color: #FAFAFA;
    line-height: 1;
}
.rec-title { color: #FAFAFA; font-weight: 600; font-size: 0.95rem; margin-right: 2rem; }
.rec-meta  { color: #718096; font-size: 0.8rem; margin-top: 0.4rem; display: flex; gap: 0.8rem; align-items: center; flex-wrap: wrap; }

/* Impact badges */
.badge {
    display: inline-block;
    border-radius: 4px;
    padding: 0.15rem 0.55rem;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.badge-high   { background: #00D4AA22; color: #00D4AA; border: 1px solid #00D4AA44; }
.badge-medium { background: #FFB34722; color: #FFB347; border: 1px solid #FFB34744; }
.badge-low    { background: #71809622; color: #718096; border: 1px solid #71809644; }

/* Salary gap pill */
.gap-pill {
    display: inline-block;
    border-radius: 20px;
    padding: 0.3rem 1rem;
    font-size: 0.85rem;
    font-weight: 600;
}
.gap-above { background: #00D4AA22; color: #00D4AA; border: 1px solid #00D4AA44; }
.gap-below { background: #FF6B6B22; color: #FF6B6B; border: 1px solid #FF6B6B44; }
.gap-at    { background: #6C63FF22; color: #A78BFA;  border: 1px solid #6C63FF44; }

/* Разделитель */
.divider {
    border: none;
    border-top: 1px solid #2D3748;
    margin: 1.5rem 0;
}

/* Зона загрузки */
.upload-hint {
    color: #718096;
    font-size: 0.85rem;
    text-align: center;
    margin-top: 0.5rem;
}

/* Прогресс шагов */
.step-item {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.4rem 0;
    color: #718096;
    font-size: 0.9rem;
}
.step-item.done   { color: #00D4AA; }
.step-item.active { color: #6C63FF; font-weight: 600; }

/* Stat row in CV Summary */
.stat-row {
    display: flex;
    align-items: baseline;
    gap: 0.4rem;
    margin-bottom: 0.8rem;
}
.stat-big   { font-size: 2.5rem; font-weight: 800; color: #6C63FF; line-height: 1; }
.stat-unit  { color: #718096; font-size: 0.9rem; }

/* Salary compare row */
.salary-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 0;
    border-bottom: 1px solid #2D374844;
}
.salary-row:last-child { border-bottom: none; }
.salary-label { color: #718096; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; }
.salary-you   { color: #FAFAFA; font-size: 1.1rem; font-weight: 700; }
.salary-market{ color: #A78BFA; font-size: 1.1rem; font-weight: 600; }
</style>
""", unsafe_allow_html=True)


# ── Хелперы ──────────────────────────────────────────────────────────────────

def file_hash(file_bytes: bytes) -> str:
    return hashlib.md5(file_bytes).hexdigest()


def format_czk(amount: int) -> str:
    return f"{amount:,}".replace(",", "\u00a0") + " CZK"


def get_score_color(score: int) -> str:
    if score >= 70:
        return "success"
    if score >= 45:
        return "warning"
    return "accent"


def render_tags(items: list[str], css_class: str = "tag") -> str:
    return " ".join(f'<span class="{css_class}">{item}</span>' for item in items)


def impact_badge(impact: str) -> str:
    return f'<span class="badge badge-{impact}">{impact}</span>'


@st.cache_data(show_spinner=False)
def call_analyze(file_bytes: bytes, filename: str, api_key: str, _hash: str) -> dict:
    """Кэшированный вызов API — повторная загрузка того же файла не триггерит LLM."""
    headers = {"X-Api-Key": api_key} if api_key else {}
    with httpx.Client(timeout=120) as client:
        response = client.post(
            f"{BASE_URL}/analyze",
            files={"file": (filename, file_bytes)},
            headers=headers,
        )
    response.raise_for_status()
    return response.json()


def check_health() -> bool:
    try:
        r = httpx.get(f"{BASE_URL}/health", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


@st.cache_data(ttl=300, show_spinner=False)
def get_benchmarks() -> dict | None:
    try:
        r = httpx.get(f"{BASE_URL}/salary-benchmarks", timeout=5)
        return r.json()
    except Exception:
        return None


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### ◆ Settings")

    api_key_input = st.text_input(
        "Anthropic API Key",
        type="password",
        placeholder="sk-ant-...",
        help="Required if ANTHROPIC_API_KEY is not set in .env",
    )

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    is_online = check_health()
    status_color = "#00D4AA" if is_online else "#FF6B6B"
    status_text = "API Online" if is_online else "API Offline"
    st.markdown(
        f'<span style="color:{status_color}; font-size:0.85rem;">● {status_text}</span>',
        unsafe_allow_html=True,
    )

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.markdown("### Market Benchmarks")

    benchmarks = get_benchmarks()
    if benchmarks:
        ranges = benchmarks.get("salary_ranges", {})
        for level, data in ranges.items():
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;'
                f'font-size:0.8rem;padding:0.2rem 0;">'
                f'<span style="color:#718096;text-transform:capitalize">{level}</span>'
                f'<span style="color:#A78BFA">{data["median"]:,}\u00a0CZK</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.caption("Start backend to see benchmarks")

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.markdown(
        '<span style="color:#718096;font-size:0.75rem;">Chain of Thought Pipeline<br>'
        'Powered by claude-sonnet-4-5</span>',
        unsafe_allow_html=True,
    )


# ── Заголовок ─────────────────────────────────────────────────────────────────

st.markdown('<div class="hero-title">Job Fit & Salary Estimator</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-subtitle">Upload a CV — get seniority score, salary range, '
    'and a personalized growth plan powered by AI</div>',
    unsafe_allow_html=True,
)

# ── Инициализация session state ───────────────────────────────────────────────

if "result" not in st.session_state:
    st.session_state.result = None
if "error" not in st.session_state:
    st.session_state.error = None

# ── Фаза 1: Upload ────────────────────────────────────────────────────────────

if st.session_state.result is None:
    uploaded = st.file_uploader(
        "Drop your CV here",
        type=["pdf", "docx"],
        label_visibility="collapsed",
    )
    st.markdown('<div class="upload-hint">PDF or DOCX · max 5 MB</div>', unsafe_allow_html=True)

    if st.session_state.error:
        st.error(st.session_state.error)
        st.session_state.error = None

    if uploaded:
        col_btn, col_info = st.columns([1, 3])
        with col_btn:
            analyze_clicked = st.button("Analyze CV", type="primary", use_container_width=True)
        with col_info:
            st.markdown(
                f'<span style="color:#718096;font-size:0.85rem;line-height:2.5rem;">'
                f'📄 {uploaded.name} · {len(uploaded.getvalue()) // 1024} KB</span>',
                unsafe_allow_html=True,
            )

        if analyze_clicked:
            file_bytes = uploaded.getvalue()

            progress_bar = st.progress(0)
            status_box = st.empty()
            steps_box = st.empty()

            STEP_LABELS = {
                1: "Extracting CV facts",
                2: "Evaluating seniority",
                3: "Calculating salary",
                4: "Generating recommendations",
            }

            def render_steps(current: int, done_steps: list[int]) -> str:
                html = ""
                for num, label in STEP_LABELS.items():
                    if num in done_steps:
                        css = "done"
                        icon = "✓"
                    elif num == current:
                        css = "active"
                        icon = "⟳"
                    else:
                        css = ""
                        icon = "○"
                    html += f'<div class="step-item {css}">{icon} Step {num}: {label}</div>'
                return html

            try:
                headers = {"X-Api-Key": api_key_input} if api_key_input else {}
                done_steps: list[int] = []
                result = None

                with httpx.Client(timeout=180) as client:
                    with client.stream(
                        "POST",
                        f"{BASE_URL}/analyze/stream",
                        files={"file": (uploaded.name, file_bytes)},
                        headers=headers,
                    ) as response:
                        response.raise_for_status()
                        for line in response.iter_lines():
                            if not line.startswith("data: "):
                                continue
                            event = _json.loads(line[6:])

                            if event.get("step") == "error":
                                raise Exception(event.get("message", "Unknown error"))

                            if event.get("step") == "done":
                                result = event["result"]
                                progress_bar.progress(100)
                                steps_box.markdown(
                                    render_steps(0, list(STEP_LABELS.keys())),
                                    unsafe_allow_html=True,
                                )
                                status_box.markdown(
                                    '<div class="step-item done">✓ Analysis complete!</div>',
                                    unsafe_allow_html=True,
                                )
                            else:
                                step_num = event["step"]
                                progress = event.get("progress", 0)
                                label = event.get("label", "")
                                # Все предыдущие шаги — завершены
                                done_steps = list(range(1, step_num))
                                progress_bar.progress(progress)
                                steps_box.markdown(
                                    render_steps(step_num, done_steps),
                                    unsafe_allow_html=True,
                                )
                                status_box.markdown(
                                    f'<div class="step-item active">⟳ {label}</div>',
                                    unsafe_allow_html=True,
                                )

                if result:
                    st.session_state.result = result
                    st.rerun()

            except httpx.HTTPStatusError as e:
                try:
                    detail = e.response.json().get("detail", str(e))
                except Exception:
                    detail = f"HTTP {e.response.status_code}: {e.response.text[:300] or str(e)}"
                st.session_state.error = f"API Error: {detail}"
                st.rerun()
            except Exception as e:
                st.session_state.error = f"Error: {e}"
                st.rerun()

# ── Фаза 2: Results ───────────────────────────────────────────────────────────

else:
    r = st.session_state.result

    cv = r["cv_facts"]
    seniority = r["seniority"]
    salary = r["salary"]
    recs = r["recommendations"]

    # ── KPI метрики ───────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)

    score_class = get_score_color(seniority["score"])
    with col1:
        st.markdown(
            f'<div class="kpi-card">'
            f'<div class="kpi-label">Seniority Score</div>'
            f'<div class="kpi-value {score_class}">{seniority["score"]}</div>'
            f'<div style="color:#718096;font-size:0.7rem">out of 100</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f'<div class="kpi-card">'
            f'<div class="kpi-label">Level</div>'
            f'<div class="kpi-value accent">{seniority["level"].capitalize()}</div>'
            f'<div style="color:#718096;font-size:0.7rem">confidence: {seniority["confidence"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col3:
        est = salary["estimated_range"]
        range_str = f'{est["min_czk"] // 1000}–{est["max_czk"] // 1000}k'
        st.markdown(
            f'<div class="kpi-card">'
            f'<div class="kpi-label">Salary Range</div>'
            f'<div class="kpi-value success">{range_str}</div>'
            f'<div style="color:#718096;font-size:0.7rem">CZK / month</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col4:
        target = recs["target_salary_czk"]
        st.markdown(
            f'<div class="kpi-card">'
            f'<div class="kpi-label">Target +30%</div>'
            f'<div class="kpi-value warning">{target // 1000}k</div>'
            f'<div style="color:#718096;font-size:0.7rem">CZK / month</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ── Вкладки ───────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs(["CV Summary", "Seniority", "Salary", "Growth Plan"])

    # ── Tab 1: CV Summary ─────────────────────────────────────────────────────
    with tab1:
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Experience**")
            st.markdown(
                f'<div class="stat-row">'
                f'<span class="stat-big">{cv["total_years_experience"]}</span>'
                f'<span class="stat-unit">years total experience</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

            st.markdown("**Education**")
            edu = cv["education_level"].replace("_", " ").title()
            st.markdown(
                f'<span class="tag" style="font-size:0.9rem;padding:0.3rem 0.8rem">{edu}</span>',
                unsafe_allow_html=True,
            )

            if cv["industries"]:
                st.markdown("**Industries**")
                st.markdown(render_tags(cv["industries"], "tag-soft"), unsafe_allow_html=True)

        with col_b:
            st.markdown("**Technical Skills**")
            skill_tags = [
                f'{s["name"]} <span style="opacity:0.5">{s["years_experience"]}y</span>'
                for s in cv["tech_skills"]
            ]
            st.markdown(
                " ".join(f'<span class="tag">{t}</span>' for t in skill_tags),
                unsafe_allow_html=True,
            )

            if cv["soft_skills"]:
                st.markdown("**Soft Skills**")
                st.markdown(render_tags(cv["soft_skills"], "tag-soft"), unsafe_allow_html=True)

        if cv["notable_achievements"]:
            st.markdown("<hr class='divider'>", unsafe_allow_html=True)
            st.markdown("**Notable Achievements**")
            for ach in cv["notable_achievements"]:
                st.markdown(
                    f'<div style="padding:0.3rem 0;color:#FAFAFA">◆ {ach}</div>',
                    unsafe_allow_html=True,
                )

    # ── Tab 2: Seniority ──────────────────────────────────────────────────────
    with tab2:
        score = seniority["score"]
        level = seniority["level"]
        score_color = "#00D4AA" if score >= 70 else "#FFB347" if score >= 45 else "#6C63FF"

        levels_order = ["intern", "junior", "mid", "senior", "lead", "principal"]
        level_ranges = {
            "intern":    (10,  29),
            "junior":    (30,  49),
            "mid":       (50,  69),
            "senior":    (70,  84),
            "lead":      (85,  94),
            "principal": (95, 100),
        }
        current_idx = levels_order.index(level) if level in levels_order else 0

        # ── Верхняя строка: score + прогресс-бар уровней ──────────────────────
        col_num, col_ladder = st.columns([1, 3])

        with col_num:
            st.markdown(
                f'<div style="text-align:center;padding:1rem 0">'
                f'<div style="font-size:6rem;font-weight:900;color:{score_color};'
                f'line-height:1;letter-spacing:-3px">{score}</div>'
                f'<div style="color:#718096;font-size:0.9rem;margin-top:0.4rem">out of 100</div>'
                f'<div style="margin-top:0.6rem">'
                f'<span style="background:{score_color}22;color:{score_color};'
                f'border:1px solid {score_color}55;border-radius:20px;'
                f'padding:0.25rem 1rem;font-size:0.85rem;font-weight:700">'
                f'{level.capitalize()}</span>'
                f'</div>'
                f'<div style="color:#718096;font-size:0.75rem;margin-top:0.5rem">'
                f'Confidence: {seniority["confidence"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        with col_ladder:
            # Горизонтальная лесенка уровней
            ladder_html = '<div style="padding:1.5rem 0 0.5rem">'
            for i, lvl in enumerate(levels_order):
                is_active = lvl == level
                is_passed = i < current_idx
                lvl_min, lvl_max = level_ranges[lvl]

                if is_active:
                    bg = score_color
                    text_col = "#0F1117"
                    sub_col = "#0F1117"
                    opacity = "1"
                    shadow = f"box-shadow:0 0 12px {score_color}55;"
                elif is_passed:
                    bg = score_color + "33"
                    text_col = score_color
                    sub_col = score_color + "aa"
                    opacity = "0.9"
                    shadow = ""
                else:
                    bg = "#1E2535"
                    text_col = "#4A5568"
                    sub_col = "#4A5568"
                    opacity = "0.6"
                    shadow = ""

                ladder_html += (
                    f'<div style="display:inline-block;vertical-align:bottom;'
                    f'margin-right:0.5rem;margin-bottom:0.5rem;opacity:{opacity}">'
                    f'<div style="background:{bg};border-radius:8px;{shadow}'
                    f'padding:0.5rem 0.9rem;text-align:center;min-width:80px">'
                    f'<div style="color:{text_col};font-weight:700;font-size:0.85rem">'
                    f'{lvl.capitalize()}</div>'
                    f'<div style="color:{sub_col};font-size:0.7rem;margin-top:0.1rem">'
                    f'{lvl_min}–{lvl_max}</div>'
                    f'</div>'
                    f'</div>'
                )
            ladder_html += '</div>'
            st.markdown(ladder_html, unsafe_allow_html=True)

            # Score-bar: визуальная полоска 0–100
            bar_pct = min(score, 100)
            st.markdown(
                f'<div style="background:#1E2535;border-radius:4px;height:8px;'
                f'margin-bottom:0.3rem;overflow:hidden">'
                f'<div style="width:{bar_pct}%;height:100%;background:{score_color};'
                f'border-radius:4px;transition:width 0.5s ease"></div>'
                f'</div>'
                f'<div style="display:flex;justify-content:space-between;'
                f'color:#4A5568;font-size:0.7rem"><span>0</span><span>100</span></div>',
                unsafe_allow_html=True,
            )

        st.markdown("<hr class='divider'>", unsafe_allow_html=True)

        # ── Нижняя строка: Strengths | Areas to Improve ───────────────────────
        col_str, col_weak = st.columns(2)

        with col_str:
            strengths = seniority.get("strengths", [])
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.8rem">'
                f'<span style="background:#00D4AA22;color:#00D4AA;border:1px solid #00D4AA44;'
                f'border-radius:4px;padding:0.15rem 0.5rem;font-size:0.75rem;font-weight:700">'
                f'✓ {len(strengths)}</span>'
                f'<span style="font-weight:700;color:#FAFAFA">Strengths</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            for s in strengths:
                st.markdown(
                    f'<div style="background:#00D4AA0D;border-left:3px solid #00D4AA;'
                    f'border-radius:0 6px 6px 0;padding:0.5rem 0.8rem;'
                    f'margin-bottom:0.4rem;color:#E2E8F0;font-size:0.88rem">'
                    f'{s}</div>',
                    unsafe_allow_html=True,
                )

        with col_weak:
            weaknesses = seniority.get("weaknesses", [])
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.8rem">'
                f'<span style="background:#FFB34722;color:#FFB347;border:1px solid #FFB34744;'
                f'border-radius:4px;padding:0.15rem 0.5rem;font-size:0.75rem;font-weight:700">'
                f'△ {len(weaknesses)}</span>'
                f'<span style="font-weight:700;color:#FAFAFA">Areas to Improve</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            for w in weaknesses:
                st.markdown(
                    f'<div style="background:#FFB3470D;border-left:3px solid #FFB347;'
                    f'border-radius:0 6px 6px 0;padding:0.5rem 0.8rem;'
                    f'margin-bottom:0.4rem;color:#E2E8F0;font-size:0.88rem">'
                    f'{w}</div>',
                    unsafe_allow_html=True,
                )

        with st.expander("Full reasoning"):
            st.write(seniority["reasoning"])

    # ── Tab 3: Salary ─────────────────────────────────────────────────────────
    with tab3:
        est = salary["estimated_range"]
        market = salary["market_range_for_level"]

        # Salary gap indicator
        gap_pct = round((est["median_czk"] - market["median_czk"]) / market["median_czk"] * 100, 1)
        if gap_pct > 2:
            gap_class = "gap-above"
            gap_text = f"▲ {gap_pct:+.1f}% above market median"
        elif gap_pct < -2:
            gap_class = "gap-below"
            gap_text = f"▼ {gap_pct:.1f}% below market median"
        else:
            gap_class = "gap-at"
            gap_text = "≈ At market median"

        st.markdown(
            f'<div style="margin-bottom:1.2rem">'
            f'<span class="gap-pill {gap_class}">{gap_text}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        col_compare, col_chart = st.columns([1, 2])

        with col_compare:
            st.markdown("**Min / Median / Max**")
            rows = [
                ("Min",    est["min_czk"],    market["min_czk"]),
                ("Median", est["median_czk"], market["median_czk"]),
                ("Max",    est["max_czk"],    market["max_czk"]),
            ]
            header = (
                '<div class="salary-row">'
                '<span class="salary-label" style="flex:1"></span>'
                '<span class="salary-you" style="font-size:0.75rem;color:#A78BFA;margin-right:1rem">You</span>'
                '<span class="salary-market" style="font-size:0.75rem;color:#6C63FF">Market</span>'
                '</div>'
            )
            st.markdown(header, unsafe_allow_html=True)
            for label, you_val, mkt_val in rows:
                st.markdown(
                    f'<div class="salary-row">'
                    f'<span class="salary-label" style="flex:1">{label}</span>'
                    f'<span class="salary-you" style="margin-right:1rem">{you_val // 1000}k</span>'
                    f'<span class="salary-market">{mkt_val // 1000}k</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            st.markdown(
                f'<div style="margin-top:1rem;padding-top:0.8rem;border-top:1px solid #2D3748">'
                f'<div style="color:#718096;font-size:0.75rem;text-transform:uppercase;'
                f'letter-spacing:0.05em">Market Fit Score</div>'
                f'<div style="font-size:2rem;font-weight:800;color:#6C63FF;margin-top:0.2rem">'
                f'{salary["fit_score"]}<span style="font-size:1rem;color:#718096">/100</span></div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        with col_chart:
            st.markdown("**Your Range vs Market**")
            import pandas as pd
            chart_df = pd.DataFrame({
                "You":    [est["min_czk"],    est["median_czk"],    est["max_czk"]],
                "Market": [market["min_czk"], market["median_czk"], market["max_czk"]],
            }, index=["Min", "Median", "Max"])
            st.bar_chart(chart_df, color=["#00D4AA", "#6C63FF"])

        if salary["top_skills_driving_salary"]:
            st.markdown("<hr class='divider'>", unsafe_allow_html=True)
            st.markdown("**Top skills driving your salary**")
            st.markdown(
                render_tags(salary["top_skills_driving_salary"]),
                unsafe_allow_html=True,
            )

        with st.expander("Salary reasoning"):
            st.write(salary["salary_reasoning"])

    # ── Tab 4: Growth Plan ────────────────────────────────────────────────────
    with tab4:
        target = recs["target_salary_czk"]
        current_median = est["median_czk"]

        col_target, col_current = st.columns(2)
        with col_target:
            st.markdown(
                f'<div class="kpi-card">'
                f'<div class="kpi-label">Target Salary (+30%)</div>'
                f'<div class="kpi-value warning">{format_czk(target)}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with col_current:
            st.markdown(
                f'<div class="kpi-card">'
                f'<div class="kpi-label">Current Median</div>'
                f'<div class="kpi-value success">{format_czk(current_median)}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown("<hr class='divider'>", unsafe_allow_html=True)
        st.markdown("**Recommendations**")

        for i, rec in enumerate(recs["recommendations"], 1):
            impact = rec["impact"]
            st.markdown(
                f'<div class="rec-card {impact}">'
                f'<div class="rec-number">{i}</div>'
                f'<div class="rec-title">{rec["action"]}</div>'
                f'<div class="rec-meta">'
                f'{impact_badge(impact)}'
                f'<span>⏱ {rec["timeframe_months"]} months</span>'
                f'<span style="color:#00D4AA">📈 +{rec["expected_salary_increase_pct"]}%</span>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        with st.expander("Full growth narrative"):
            st.write(recs["narrative"])

    # ── Нижняя панель ─────────────────────────────────────────────────────────
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    col_reset, col_download, col_time = st.columns([1, 1, 2])
    with col_reset:
        if st.button("Analyze Another CV", use_container_width=True):
            st.session_state.result = None
            call_analyze.clear()
            st.rerun()
    with col_download:
        st.download_button(
            label="Download Report (JSON)",
            data=_json.dumps(r, indent=2, ensure_ascii=False),
            file_name=f"cv_analysis_{cv.get('full_name', 'report').replace(' ', '_')}.json",
            mime="application/json",
            use_container_width=True,
        )
    with col_time:
        proc_time = r.get("processing_time_seconds", 0)
        st.markdown(
            f'<span style="color:#718096;font-size:0.8rem;line-height:2.5rem;">'
            f'⚡ Analyzed in {proc_time:.1f}s · Chain of Thought · 4 LLM steps</span>',
            unsafe_allow_html=True,
        )
