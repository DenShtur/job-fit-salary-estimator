import hashlib
import time

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
/* Основная тема */
[data-testid="stAppViewContainer"] {
    background-color: #0F1117;
}
[data-testid="stSidebar"] {
    background-color: #161B27;
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
.kpi-value.accent { color: #6C63FF; }
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
    border-left: 3px solid #6C63FF;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
}
.rec-card.high  { border-left-color: #00D4AA; }
.rec-card.medium { border-left-color: #FFB347; }
.rec-card.low   { border-left-color: #718096; }

.rec-title { color: #FAFAFA; font-weight: 600; font-size: 0.95rem; }
.rec-meta  { color: #718096; font-size: 0.8rem; margin-top: 0.3rem; }

/* Impact badges */
.badge {
    display: inline-block;
    border-radius: 4px;
    padding: 0.1rem 0.5rem;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
}
.badge-high   { background: #00D4AA22; color: #00D4AA; }
.badge-medium { background: #FFB34722; color: #FFB347; }
.badge-low    { background: #71809622; color: #718096; }

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
.step-item.done  { color: #00D4AA; }
.step-item.active { color: #6C63FF; font-weight: 600; }
</style>
""", unsafe_allow_html=True)


# ── Хелперы ──────────────────────────────────────────────────────────────────

def file_hash(file_bytes: bytes) -> str:
    return hashlib.md5(file_bytes).hexdigest()


def format_czk(amount: int) -> str:
    return f"{amount:,}".replace(",", " ") + " CZK"


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
                f'<span style="color:#A78BFA">{data["median"]:,} CZK</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.caption("Start backend to see benchmarks")

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.markdown(
        '<span style="color:#718096;font-size:0.75rem;">Chain of Thought Pipeline<br>'
        'Powered by Claude 3.5 Sonnet</span>',
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
            fhash = file_hash(file_bytes)

            steps = [
                "Extracting CV facts...",
                "Evaluating seniority...",
                "Calculating salary...",
                "Generating recommendations...",
            ]

            progress_bar = st.progress(0)
            status_box = st.empty()

            try:
                for i, step in enumerate(steps):
                    status_box.markdown(
                        f'<div class="step-item active">⟳ {step}</div>',
                        unsafe_allow_html=True,
                    )
                    progress_bar.progress((i + 1) * 20)
                    if i == 0:
                        # Запускаем реальный вызов на первом шаге
                        result = call_analyze(
                            file_bytes,
                            uploaded.name,
                            api_key_input or "",
                            fhash,
                        )
                    else:
                        time.sleep(0.4)  # визуальная анимация шагов

                progress_bar.progress(100)
                status_box.markdown(
                    '<div class="step-item done">✓ Analysis complete!</div>',
                    unsafe_allow_html=True,
                )
                time.sleep(0.5)
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

    # KPI метрики
    col1, col2, col3, col4 = st.columns(4)

    score_class = get_score_color(seniority["score"])
    with col1:
        st.markdown(
            f'<div class="kpi-card">'
            f'<div class="kpi-label">Seniority Score</div>'
            f'<div class="kpi-value {score_class}">{seniority["score"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f'<div class="kpi-card">'
            f'<div class="kpi-label">Level</div>'
            f'<div class="kpi-value accent">{seniority["level"].capitalize()}</div>'
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

    # Вкладки
    tab1, tab2, tab3, tab4 = st.tabs(["CV Summary", "Seniority", "Salary", "Growth Plan"])

    # ── Tab 1: CV Summary ─────────────────────────────────────────────────────
    with tab1:
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Experience**")
            st.markdown(
                f'<span style="font-size:2rem;font-weight:700;color:#6C63FF">'
                f'{cv["total_years_experience"]}</span>'
                f'<span style="color:#718096"> years</span>',
                unsafe_allow_html=True,
            )

            st.markdown("**Education**")
            edu = cv["education_level"].replace("_", " ").title()
            st.markdown(
                f'<span class="tag">{edu}</span>',
                unsafe_allow_html=True,
            )

            st.markdown("**Industries**")
            st.markdown(
                render_tags(cv["industries"], "tag-soft"),
                unsafe_allow_html=True,
            )

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

            st.markdown("**Soft Skills**")
            st.markdown(
                render_tags(cv["soft_skills"], "tag-soft"),
                unsafe_allow_html=True,
            )

        if cv["notable_achievements"]:
            st.markdown("**Notable Achievements**")
            for ach in cv["notable_achievements"]:
                st.markdown(f"- {ach}")

    # ── Tab 2: Seniority ──────────────────────────────────────────────────────
    with tab2:
        col_score, col_detail = st.columns([1, 2])

        with col_score:
            score = seniority["score"]
            level = seniority["level"]
            score_color = "#00D4AA" if score >= 70 else "#FFB347" if score >= 45 else "#6C63FF"

            # Термометр уровней
            levels = ["intern", "junior", "mid", "senior", "lead", "principal"]
            level_scores = {"intern": 10, "junior": 30, "mid": 50, "senior": 70, "lead": 85, "principal": 95}

            thermometer_html = '<div style="margin:1.5rem 0">'
            for lvl in reversed(levels):
                is_active = lvl == level
                is_passed = level_scores.get(level, 0) > level_scores.get(lvl, 0)
                if is_active:
                    bg = score_color
                    text_color = "#0F1117"
                    border = f"2px solid {score_color}"
                    font_weight = "700"
                    label_color = score_color
                elif is_passed:
                    bg = score_color + "33"
                    text_color = score_color
                    border = f"1px solid {score_color}55"
                    font_weight = "400"
                    label_color = "#718096"
                else:
                    bg = "#1E2535"
                    text_color = "#4A5568"
                    border = "1px solid #2D3748"
                    font_weight = "400"
                    label_color = "#4A5568"

                thermometer_html += (
                    f'<div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.4rem">'
                    f'<div style="background:{bg};border:{border};border-radius:6px;'
                    f'padding:0.3rem 0.8rem;min-width:80px;text-align:center;'
                    f'color:{text_color};font-weight:{font_weight};font-size:0.85rem">'
                    f'{lvl.capitalize()}</div>'
                    f'<div style="color:{label_color};font-size:0.75rem">'
                    f'{level_scores[lvl]}–{"100" if lvl == "principal" else str(level_scores[levels[levels.index(lvl)+1]]-1) if levels.index(lvl) < len(levels)-1 else "100"} pts'
                    f'</div>'
                    f'</div>'
                )
            thermometer_html += '</div>'

            st.markdown(
                f'<div style="text-align:center;padding:1rem 0">'
                f'<div style="font-size:4.5rem;font-weight:900;color:{score_color}">'
                f'{score}</div>'
                f'<div style="color:#718096;font-size:0.85rem">out of 100</div>'
                f'<div style="color:#718096;font-size:0.75rem;margin-top:0.3rem">'
                f'Confidence: {seniority["confidence"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.markdown(thermometer_html, unsafe_allow_html=True)

        with col_detail:
            st.markdown("**Strengths**")
            for s in seniority["strengths"]:
                st.markdown(
                    f'<div style="color:#00D4AA;padding:0.2rem 0">✓ {s}</div>',
                    unsafe_allow_html=True,
                )

            st.markdown("**Areas to Improve**")
            for w in seniority["weaknesses"]:
                st.markdown(
                    f'<div style="color:#FFB347;padding:0.2rem 0">△ {w}</div>',
                    unsafe_allow_html=True,
                )

        with st.expander("Full reasoning"):
            st.write(seniority["reasoning"])

    # ── Tab 3: Salary ─────────────────────────────────────────────────────────
    with tab3:
        est = salary["estimated_range"]
        market = salary["market_range_for_level"]

        col_chart, col_info = st.columns([2, 1])

        with col_chart:
            st.markdown("**Your Range vs Market**")
            chart_data = {
                "You (min)": est["min_czk"],
                "You (median)": est["median_czk"],
                "You (max)": est["max_czk"],
                "Market (min)": market["min_czk"],
                "Market (median)": market["median_czk"],
                "Market (max)": market["max_czk"],
            }
            st.bar_chart(chart_data, color="#6C63FF")

        with col_info:
            st.markdown("**Your Estimate**")
            st.markdown(
                f'<div style="padding:0.8rem 0">'
                f'<div style="color:#718096;font-size:0.75rem">MIN</div>'
                f'<div style="font-size:1.3rem;font-weight:700;color:#FAFAFA">'
                f'{format_czk(est["min_czk"])}</div>'
                f'<div style="color:#718096;font-size:0.75rem;margin-top:0.5rem">MEDIAN</div>'
                f'<div style="font-size:1.3rem;font-weight:700;color:#00D4AA">'
                f'{format_czk(est["median_czk"])}</div>'
                f'<div style="color:#718096;font-size:0.75rem;margin-top:0.5rem">MAX</div>'
                f'<div style="font-size:1.3rem;font-weight:700;color:#FAFAFA">'
                f'{format_czk(est["max_czk"])}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                f'<div style="margin-top:1rem">'
                f'<div style="color:#718096;font-size:0.75rem">MARKET FIT SCORE</div>'
                f'<div style="font-size:1.8rem;font-weight:700;color:#6C63FF">'
                f'{salary["fit_score"]}/100</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

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

        for rec in recs["recommendations"]:
            impact = rec["impact"]
            st.markdown(
                f'<div class="rec-card {impact}">'
                f'<div class="rec-title">{rec["action"]}</div>'
                f'<div class="rec-meta">'
                f'{impact_badge(impact)} &nbsp;'
                f'⏱ {rec["timeframe_months"]} months &nbsp;'
                f'📈 +{rec["expected_salary_increase_pct"]}%'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        with st.expander("Full growth narrative"):
            st.write(recs["narrative"])

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    col_reset, col_download, col_time = st.columns([1, 1, 2])
    with col_reset:
        if st.button("Analyze Another CV", use_container_width=True):
            st.session_state.result = None
            call_analyze.clear()
            st.rerun()
    with col_download:
        import json as _json
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
