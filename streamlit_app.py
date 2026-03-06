"""
CRYSYS v3.0 - Enhanced Streamlit Frontend
All Visual Improvements Implemented:
- Color-coded gradient cards
- Interactive timeline with hover
- Enhanced error cards with previews
- Visual health meters
- Sticky summary bar
- Dark/Light mode toggle
- Better charts and filtering
- Smooth animations
"""

import streamlit as st
import sys
import os
from pathlib import Path
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from io import BytesIO
from collections import defaultdict
import re

# Add backend to path
sys.path.append(str(Path(__file__).parent / 'backend'))
from crysys_v3 import UltimateCRYSYS
from error_grouper import ErrorGrouper
from timeline_analyzer import TimelineAnalyzer
from export_utils import ExportUtils

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="CRYSYS v3.0 - Log Analysis",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# SESSION STATE
# ============================================================================

if 'results' not in st.session_state:
    st.session_state.results = None
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'alert_rules' not in st.session_state:
    st.session_state.alert_rules = []
if 'triggered_alerts' not in st.session_state:
    st.session_state.triggered_alerts = []
if 'grouped_errors' not in st.session_state:
    st.session_state.grouped_errors = None
if 'timeline_data' not in st.session_state:
    st.session_state.timeline_data = None
if 'theme_mode' not in st.session_state:
    st.session_state.theme_mode = 'dark'
if 'view_mode_compact' not in st.session_state:
    st.session_state.view_mode_compact = False

# ============================================================================
# ENHANCED CUSTOM CSS
# ============================================================================

st.markdown("""
<style>
    /* Main Header with Animation */
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
        animation: fadeIn 0.8s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Sticky Summary Bar */
    .sticky-summary {
        position: sticky;
        top: 0;
        z-index: 999;
        background: linear-gradient(135deg, #1a2332 0%, #0f1419 100%);
        padding: 12px 20px;
        border-bottom: 2px solid #667eea;
        backdrop-filter: blur(10px);
        display: flex;
        justify-content: space-around;
        align-items: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        margin-bottom: 20px;
    }
    
    .sticky-item {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.9rem;
    }
    
    .sticky-critical { color: #f56565; font-weight: bold; }
    .sticky-high { color: #ed8936; font-weight: bold; }
    .sticky-info { color: #a0aec0; }
    
    /* Enhanced Metric Cards with Gradients */
    .metric-card-critical {
        background: linear-gradient(135deg, #f56565 0%, #c53030 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        box-shadow: 0 8px 16px rgba(245, 101, 101, 0.3);
        transition: transform 0.3s, box-shadow 0.3s;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { box-shadow: 0 8px 16px rgba(245, 101, 101, 0.3); }
        50% { box-shadow: 0 8px 24px rgba(245, 101, 101, 0.6); }
    }
    
    .metric-card-critical:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 24px rgba(245, 101, 101, 0.5);
    }
    
    .metric-card-warning {
        background: linear-gradient(135deg, #ed8936 0%, #c05621 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        box-shadow: 0 4px 12px rgba(237, 137, 54, 0.3);
        transition: transform 0.3s;
    }
    
    .metric-card-warning:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 16px rgba(237, 137, 54, 0.5);
    }
    
    .metric-card-info {
        background: linear-gradient(135deg, #667eea 0%, #4c51bf 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
        transition: transform 0.3s;
    }
    
    .metric-card-info:hover {
        transform: translateY(-4px);
    }
    
    .metric-card-success {
        background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        box-shadow: 0 4px 12px rgba(72, 187, 120, 0.2);
        transition: transform 0.3s;
    }
    
    .metric-number {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 8px 0;
    }
    
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .metric-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        background: rgba(255,255,255,0.2);
        font-size: 0.75rem;
        margin-top: 8px;
    }
    
    /* Enhanced Error Cards */
    .error-card {
        border-radius: 12px;
        padding: 16px;
        margin: 12px 0;
        border-left: 6px solid;
        background: linear-gradient(135deg, #1a2332 0%, #0f1419 100%);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }
    
    .error-card:hover {
        transform: translateX(8px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3);
    }
    
    .error-card-critical {
        border-left-color: #f56565;
        background: linear-gradient(135deg, rgba(245, 101, 101, 0.1) 0%, #1a2332 100%);
    }
    
    .error-card-high {
        border-left-color: #ed8936;
        background: linear-gradient(135deg, rgba(237, 137, 54, 0.1) 0%, #1a2332 100%);
    }
    
    .error-card-medium {
        border-left-color: #ecc94b;
        background: linear-gradient(135deg, rgba(236, 201, 75, 0.1) 0%, #1a2332 100%);
    }
    
    .error-card-low {
        border-left-color: #48bb78;
        background: linear-gradient(135deg, rgba(72, 187, 120, 0.1) 0%, #1a2332 100%);
    }
    
    .error-preview {
        font-size: 0.85rem;
        color: #a0aec0;
        margin-top: 8px;
        padding: 8px;
        background: rgba(0,0,0,0.2);
        border-radius: 6px;
    }
    
    .error-quick-fix {
        color: #48bb78;
        font-weight: 500;
    }
    
    .error-impact {
        color: #ed8936;
        font-weight: 500;
    }
    
    .occurrence-dots {
        display: inline-flex;
        gap: 3px;
        margin-left: 8px;
    }
    
    .occurrence-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #667eea;
        display: inline-block;
    }
    
    /* Context Viewer Enhanced */
    .context-viewer {
        background: #0d1117;
        border-radius: 8px;
        padding: 16px;
        font-family: 'Courier New', monospace;
        font-size: 13px;
        border: 1px solid #30363d;
        box-shadow: inset 0 2px 8px rgba(0,0,0,0.3);
    }
    
    .context-line-before {
        color: #6e7681;
        padding: 3px 8px;
        display: block;
        transition: background 0.2s;
    }
    
    .context-line-before:hover {
        background: rgba(110, 118, 129, 0.1);
    }
    
    .context-line-error {
        background: rgba(245, 101, 101, 0.15);
        color: #fc8181;
        padding: 6px 8px;
        border-left: 4px solid #f56565;
        display: block;
        font-weight: bold;
        animation: errorPulse 2s infinite;
    }
    
    @keyframes errorPulse {
        0%, 100% { background: rgba(245, 101, 101, 0.15); }
        50% { background: rgba(245, 101, 101, 0.25); }
    }
    
    .context-line-after {
        color: #6e7681;
        padding: 3px 8px;
        display: block;
        transition: background 0.2s;
    }
    
    .context-line-after:hover {
        background: rgba(110, 118, 129, 0.1);
    }
    
    .line-number {
        color: #4a5568;
        margin-right: 16px;
        min-width: 60px;
        display: inline-block;
        user-select: none;
    }
    
    /* Health Meters */
    .health-meter-container {
        margin: 12px 0;
    }
    
    .health-meter {
        height: 8px;
        background: #2d3748;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .health-meter-fill {
        height: 100%;
        border-radius: 8px;
        transition: width 0.8s ease;
        background: linear-gradient(90deg, #48bb78 0%, #38a169 100%);
    }
    
    .health-meter-fill-warning {
        background: linear-gradient(90deg, #ecc94b 0%, #d69e2e 100%);
    }
    
    .health-meter-fill-danger {
        background: linear-gradient(90deg, #f56565 0%, #e53e3e 100%);
    }
    
    /* Component Health Cards */
    .health-card {
        background: linear-gradient(135deg, #1a2332 0%, #0f1419 100%);
        border-radius: 12px;
        padding: 20px;
        margin: 12px 0;
        border: 2px solid;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }
    
    .health-card:hover {
        transform: scale(1.02);
    }
    
    .health-card-healthy {
        border-color: #48bb78;
    }
    
    .health-card-warning {
        border-color: #ed8936;
    }
    
    .health-card-critical {
        border-color: #f56565;
    }
    
    .health-emoji {
        font-size: 3rem;
        margin-bottom: 12px;
    }
    
    .health-score {
        font-size: 2rem;
        font-weight: bold;
        margin: 8px 0;
    }
    
    .health-trend {
        font-size: 1.2rem;
        margin-left: 8px;
    }
    
    /* Timeline Cards */
    .timeline-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 20px;
        color: white;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        margin: 12px 0;
    }
    
    .timeline-card-warning {
        background: linear-gradient(135deg, #ed8936 0%, #c05621 100%);
    }
    
    .timeline-card-success {
        background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
    }
    
    /* Action Buttons */
    .action-button {
        display: inline-block;
        padding: 8px 16px;
        border-radius: 6px;
        background: #667eea;
        color: white;
        text-decoration: none;
        margin: 4px;
        transition: all 0.3s;
        cursor: pointer;
        border: none;
        font-size: 0.9rem;
    }
    
    .action-button:hover {
        background: #764ba2;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(102, 126, 234, 0.4);
    }
    
    .action-button-danger {
        background: #f56565;
    }
    
    .action-button-danger:hover {
        background: #e53e3e;
    }
    
    .action-button-success {
        background: #48bb78;
    }
    
    .action-button-success:hover {
        background: #38a169;
    }
    
    /* Search Highlight */
    .search-highlight {
        background: #ecc94b;
        color: #1a202c;
        padding: 2px 4px;
        border-radius: 3px;
        font-weight: bold;
    }
    
    /* Loading Animation */
    .loading-container {
        text-align: center;
        padding: 40px;
    }
    
    .loading-spinner {
        border: 4px solid #2d3748;
        border-top: 4px solid #667eea;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        animation: spin 1s linear infinite;
        margin: 0 auto;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Breadcrumb */
    .breadcrumb {
        color: #a0aec0;
        font-size: 0.9rem;
        margin-bottom: 20px;
    }
    
    .breadcrumb a {
        color: #667eea;
        text-decoration: none;
    }
    
    .breadcrumb a:hover {
        text-decoration: underline;
    }
    
    /* Empty State */
    .empty-state {
        text-align: center;
        padding: 60px 20px;
        color: #a0aec0;
    }
    
    .empty-state-emoji {
        font-size: 4rem;
        margin-bottom: 20px;
    }
    
    /* Compact View */
    .compact-error-item {
        padding: 8px 12px;
        margin: 4px 0;
        border-left: 3px solid;
        background: rgba(26, 35, 50, 0.5);
        border-radius: 4px;
        font-size: 0.85rem;
        transition: background 0.2s;
    }
    
    .compact-error-item:hover {
        background: rgba(26, 35, 50, 0.8);
    }
    
    /* Tooltip */
    .tooltip {
        position: relative;
        display: inline-block;
    }
    
    .tooltip .tooltiptext {
        visibility: hidden;
        background-color: #2d3748;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 8px 12px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -60px;
        opacity: 0;
        transition: opacity 0.3s;
        font-size: 0.85rem;
    }
    
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_severity_color(severity: str) -> str:
    colors = {
        'CRITICAL': '#f56565',
        'HIGH': '#ed8936',
        'MEDIUM': '#ecc94b',
        'LOW': '#48bb78',
        'INFO': '#4299e1'
    }
    return colors.get(severity, '#a0aec0')


def get_severity_emoji(severity: str) -> str:
    emojis = {
        'CRITICAL': '🔴',
        'HIGH': '🟠',
        'MEDIUM': '🟡',
        'LOW': '🟢',
        'INFO': '🔵'
    }
    return emojis.get(severity, '⚪')


def get_category_icon(category: str) -> str:
    icons = {
        'DATABASE': '🗄️',
        'NULL_POINTER': '⚠️',
        'NETWORK': '🌐',
        'AUTHENTICATION': '🔐',
        'GENERIC': '📦'
    }
    return icons.get(category, '📦')


def render_occurrence_dots(count: int, max_display: int = 15):
    """Render visual dots for error occurrences"""
    dots_html = '<span class="occurrence-dots">'
    display_count = min(count, max_display)
    for i in range(display_count):
        dots_html += '<span class="occurrence-dot"></span>'
    if count > max_display:
        dots_html += f'<span style="color: #a0aec0; margin-left: 4px;">+{count - max_display}</span>'
    dots_html += '</span>'
    return dots_html


def render_health_meter(score: int):
    """Render visual health meter"""
    if score >= 75:
        fill_class = "health-meter-fill"
    elif score >= 40:
        fill_class = "health-meter-fill-warning"
    else:
        fill_class = "health-meter-fill-danger"
    
    html = f"""
    <div class="health-meter-container">
        <div class="health-meter">
            <div class="{fill_class}" style="width: {score}%;"></div>
        </div>
    </div>
    """
    return html


def auto_adjust_severity(error: dict, all_errors: list) -> str:
    """Auto-adjust severity based on context"""
    original_severity = error.get('severity', 'MEDIUM')
    component = error.get('component', '').lower()
    
    same_errors = [e for e in all_errors
                  if e.get('exception_class') == error.get('exception_class')
                  and e.get('component') == error.get('component')]
    count = len(same_errors)

    severity_order = ['INFO', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
    current_idx = severity_order.index(original_severity) if original_severity in severity_order else 2

    if count >= 10 and current_idx < 4:
        current_idx = min(current_idx + 2, 4)
    elif count >= 5 and current_idx < 4:
        current_idx = min(current_idx + 1, 4)

    if any(kw in component for kw in ['payment', 'checkout', 'billing', 'auth', 'security']):
        if current_idx < 4:
            current_idx = min(current_idx + 1, 4)

    if any(kw in component for kw in ['cache', 'log', 'metric', 'monitor', 'optional']):
        if current_idx > 0:
            current_idx = max(current_idx - 1, 0)

    adjusted = severity_order[current_idx]

    if adjusted != original_severity:
        error['severity_adjusted'] = True
        error['original_severity'] = original_severity

    return adjusted


def check_alert_rules(results: dict, rules: list) -> list:
    """Check if any alert rules are triggered"""
    triggered = []

    for rule in rules:
        matching_errors = []

        for error in results.get('error_events', []):
            severity_match = (rule['severity'] == 'ANY' or
                            error.get('severity') == rule['severity'])
            component_match = (rule['component'] == '' or
                             rule['component'].lower() in error.get('component', '').lower())
            keyword_match = (rule['keyword'] == '' or
                           rule['keyword'].lower() in error.get('message', '').lower() or
                           rule['keyword'].lower() in error.get('exception_class', '').lower())

            if severity_match and component_match and keyword_match:
                matching_errors.append(error)

        if matching_errors and len(matching_errors) >= rule.get('min_occurrences', 1):
            triggered.append({
                'rule': rule,
                'matching_errors': matching_errors,
                'count': len(matching_errors)
            })

    return triggered


def highlight_search_text(text: str, search_query: str) -> str:
    """Highlight search query in text"""
    if not search_query:
        return text
    
    pattern = re.compile(re.escape(search_query), re.IGNORECASE)
    return pattern.sub(lambda m: f'<span class="search-highlight">{m.group()}</span>', text)


def render_sticky_summary(results: dict):
    """Render sticky summary bar at top"""
    critical_count = len([e for e in results['error_events'] if e.get('severity') == 'CRITICAL'])
    high_count = len([e for e in results['error_events'] if e.get('severity') == 'HIGH'])
    total_logs = results['total_logs']
    processing_time = results.get('processing_time', 0)
    
    html = f"""
    <div class="sticky-summary">
        <div class="sticky-item sticky-critical">
            <span>🔴</span>
            <span>{critical_count} CRITICAL</span>
        </div>
        <div class="sticky-item sticky-high">
            <span>🟠</span>
            <span>{high_count} HIGH</span>
        </div>
        <div class="sticky-item sticky-info">
            <span>📄</span>
            <span>{total_logs:,} Logs</span>
        </div>
        <div class="sticky-item sticky-info">
            <span>⏱️</span>
            <span>{processing_time:.1f}s</span>
        </div>
        <div class="sticky-item sticky-info">
            <span>✅</span>
            <span>{len(results['error_events'])} Errors Found</span>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_context_viewer(error: dict, search_query: str = ""):
    """Render enhanced context viewer"""
    if not error.get('line_number'):
        st.info("📍 Line number not available for this error")
        return

    st.markdown(f"**📍 Location:** Line `{error['line_number']:,}` in log file")

    if error.get('timestamp'):
        st.markdown(f"**🕐 Timestamp:** `{error['timestamp']}`")

    before_ctx = error.get('before_context', [])
    after_ctx = error.get('after_context', [])

    if before_ctx or after_ctx:
        context_html = '<div class="context-viewer">'

        for line in before_ctx:
            line_num = line['line_number']
            content = highlight_search_text(line['content'][:200], search_query)
            context_html += f'<span class="context-line-before"><span class="line-number">{line_num}</span>{content}</span>'

        error_line = highlight_search_text(error.get("log_line", "")[:200], search_query)
        context_html += f'<span class="context-line-error"><span class="line-number">→ {error["line_number"]}</span>{error_line}</span>'

        for line in after_ctx:
            line_num = line['line_number']
            content = highlight_search_text(line['content'][:200], search_query)
            context_html += f'<span class="context-line-after"><span class="line-number">{line_num}</span>{content}</span>'

        context_html += '</div>'
        st.markdown(context_html, unsafe_allow_html=True)
    else:
        st.code(error.get('log_line', 'No log line available'), language='text')


def render_component_health(results: dict):
    """Enhanced component health dashboard with visual meters"""
    st.subheader("🏥 Component Health Dashboard")

    component_stats = defaultdict(lambda: {
        'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0, 'total': 0
    })

    for error in results.get('error_events', []):
        component = error.get('component', 'Unknown')
        severity = error.get('severity', 'LOW').lower()
        component_stats[component]['total'] += 1
        # Safely increment only if severity key exists
        if severity in component_stats[component]:
            component_stats[component][severity] += 1

    if not component_stats:
        st.info("No component data available")
        return

    def calculate_health_score(stats):
        score = 100
        score -= stats.get('critical', 0) * 25
        score -= stats.get('high', 0) * 10
        score -= stats.get('medium', 0) * 5
        score -= stats.get('low', 0) * 2
        score -= stats.get('info', 0) * 1  # Info has minimal impact
        return max(0, score)

    components_sorted = sorted(
        component_stats.items(),
        key=lambda x: calculate_health_score(x[1])
    )

    # Show needs attention banner
    critical_components = [
        (comp, calculate_health_score(stats))
        for comp, stats in components_sorted
        if calculate_health_score(stats) < 75
    ]
    
    if critical_components:
        st.warning(f"⚠️ **{len(critical_components)} Component(s) Need Attention**")

    # Display health cards in grid
    cols = st.columns(min(len(components_sorted), 3))

    for i, (component, stats) in enumerate(components_sorted):
        score = calculate_health_score(stats)
        col = cols[i % 3]

        with col:
            if score >= 75:
                health_emoji = "✅"
                health_color = "#48bb78"
                health_label = "Healthy"
                card_class = "health-card-healthy"
            elif score >= 40:
                health_emoji = "⚠️"
                health_color = "#ed8936"
                health_label = "Warning"
                card_class = "health-card-warning"
            else:
                health_emoji = "🔴"
                health_color = "#f56565"
                health_label = "Critical"
                card_class = "health-card-critical"

            html = f"""
            <div class="health-card {card_class}">
                <div class="health-emoji">{health_emoji}</div>
                <div style="font-weight: bold; color: white; font-size: 1.1rem;">{component}</div>
                <div style="color: {health_color}; font-size: 0.9rem; margin: 4px 0;">{health_label}</div>
                {render_health_meter(score)}
                <div class="health-score" style="color: {health_color};">{score}/100</div>
                <div style="color: #a0aec0; font-size: 0.8rem; margin-top: 8px;">
                    🔴 {stats['critical']} | 🟠 {stats['high']} | 🟡 {stats['medium']} | 🟢 {stats['low']} | 🔵 {stats['info']}
                </div>
            </div>
            """
            st.markdown(html, unsafe_allow_html=True)

    # Detailed table
    st.markdown("### 📊 Detailed Health Table")
    health_data = []
    for component, stats in components_sorted:
        score = calculate_health_score(stats)
        health_data.append({
            'Component': component,
            'Health Score': f"{score}/100",
            'Critical': stats['critical'],
            'High': stats['high'],
            'Medium': stats['medium'],
            'Low': stats['low'],
            'Info': stats['info'],
            'Total Errors': stats['total'],
            'Status': '🔴 Critical' if score < 40 else '⚠️ Warning' if score < 75 else '✅ Healthy'
        })

    df = pd.DataFrame(health_data)
    st.dataframe(df, use_container_width=True)


# ============================================================================
# HEADER
# ============================================================================

st.markdown('<h1 class="main-header">🔥 CRYSYS v3.0</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #718096; font-size: 1.2rem;">Ultimate Log Analysis Portal - Enhanced Edition</p>', unsafe_allow_html=True)
st.markdown("---")

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.header("⚙️ Settings")

    api_key = st.text_input(
        "Groq API Key",
        value="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",
        type="password"
    )

    enable_cache = st.checkbox("Enable Cache", value=True)
    enable_parallel = st.checkbox("Enable Parallel Processing", value=True)

    context_window = st.slider(
        "Context Window (lines before/after error)",
        min_value=2,
        max_value=10,
        value=5,
        help="How many lines to show before and after each error"
    )

    st.markdown("---")
    
    # View mode toggle
    st.subheader("🎨 Display Options")
    st.session_state.view_mode_compact = st.checkbox("Compact View", value=False)

    st.markdown("---")

    # Alert Rules Section
    st.header("🔔 Alert Rules")

    with st.expander("➕ Add New Rule"):
        rule_severity = st.selectbox("Severity", ['ANY', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'])
        rule_component = st.text_input("Component (optional)", placeholder="e.g. PaymentService")
        rule_keyword = st.text_input("Keyword (optional)", placeholder="e.g. timeout")
        rule_min_occurrences = st.number_input("Min Occurrences", min_value=1, value=1)
        rule_action = st.selectbox("Action", ['Show Alert', 'Flag as Critical', 'Highlight'])

        if st.button("Add Rule", type="primary"):
            new_rule = {
                'id': len(st.session_state.alert_rules),
                'severity': rule_severity,
                'component': rule_component,
                'keyword': rule_keyword,
                'min_occurrences': rule_min_occurrences,
                'action': rule_action
            }
            st.session_state.alert_rules.append(new_rule)
            st.success(f"✅ Rule added!")

    if st.session_state.alert_rules:
        st.markdown("**Active Rules:**")
        for i, rule in enumerate(st.session_state.alert_rules):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"Rule {i+1}: {rule['severity']} | {rule['component'] or 'Any'} | {rule['keyword'] or 'Any'}")
            with col2:
                if st.button("❌", key=f"del_rule_{i}"):
                    st.session_state.alert_rules.pop(i)
                    st.rerun()

    st.markdown("---")
    st.markdown("### 📊 About")
    st.info("CRYSYS v3.0 Enhanced Edition with visual improvements")

    if st.session_state.analysis_complete:
        if st.button("🔄 New Analysis"):
            st.session_state.results = None
            st.session_state.analysis_complete = False
            st.session_state.grouped_errors = None
            st.session_state.timeline_data = None
            st.rerun()

# ============================================================================
# MAIN CONTENT
# ============================================================================

if not st.session_state.analysis_complete:

    st.markdown('<div class="breadcrumb">Home > Upload</div>', unsafe_allow_html=True)
    
    st.header("📁 Upload Log File")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        uploaded_file = st.file_uploader(
            "Choose a log file",
            type=['log', 'txt'],
            help="Upload .log or .txt files"
        )

        if uploaded_file:
            file_size = len(uploaded_file.getvalue())
            st.success(f"✅ **{uploaded_file.name}** ({file_size / 1024 / 1024:.2f} MB)")

            with st.expander("👀 Preview First 20 Lines"):
                preview = uploaded_file.getvalue().decode('utf-8', errors='ignore').split('\n')[:20]
                st.code('\n'.join(preview))

            st.markdown("---")

            if st.button("🚀 Analyze Log File", type="primary", use_container_width=True):
                temp_path = Path("temp_upload.log")
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # Enhanced loading animation
                st.markdown("""
                <div class="loading-container">
                    <div class="loading-spinner"></div>
                    <p style="margin-top: 20px; color: #667eea; font-weight: bold;">Analyzing your logs...</p>
                </div>
                """, unsafe_allow_html=True)

                status_placeholder = st.empty()
                
                status_placeholder.info("📖 Reading log file...")
                
                with open(temp_path, 'r', encoding='utf-8', errors='ignore') as f:
                    logs = [line.strip() for line in f if line.strip()]

                status_placeholder.info(f"✅ Loaded {len(logs):,} lines")

                status_placeholder.info("🤖 Initializing CRYSYS analyzer...")

                analyzer = UltimateCRYSYS(
                    api_key=api_key,
                    enable_parallel=enable_parallel,
                    enable_cache=enable_cache,
                    enable_dashboard=False,
                    context_window=context_window
                )

                status_placeholder.info("🔍 Running AI analysis (this may take a few minutes)...")

                results = analyzer.analyze_logs(logs)

                # Post-process
                for error in results.get('error_events', []):
                    error['severity'] = auto_adjust_severity(error, results['error_events'])

                # Group errors
                grouper = ErrorGrouper()
                grouped = grouper.create_grouped_summary(results['error_events'])
                st.session_state.grouped_errors = grouped

                # Timeline analysis
                timeline_analyzer = TimelineAnalyzer()
                timeline_data = timeline_analyzer.analyze_timeline(
                    results['error_events'],
                    logs,
                    results['suspicious_indices']
                )
                st.session_state.timeline_data = timeline_data

                # Check alert rules
                if st.session_state.alert_rules:
                    triggered = check_alert_rules(results, st.session_state.alert_rules)
                    st.session_state.triggered_alerts = triggered

                results['job_id'] = datetime.now().strftime('%Y%m%d_%H%M%S')
                results['filename'] = uploaded_file.name
                results['timestamp'] = datetime.now().isoformat()

                st.session_state.results = results
                st.session_state.analysis_complete = True

                status_placeholder.success("✅ Analysis complete!")

                if temp_path.exists():
                    temp_path.unlink()

                st.balloons()
                st.rerun()

else:
    # ============================================================================
    # RESULTS DISPLAY WITH STICKY SUMMARY
    # ============================================================================

    results = st.session_state.results
    
    # Breadcrumb
    st.markdown(f'<div class="breadcrumb">Home > Results > {results.get("filename", "Analysis")}</div>', unsafe_allow_html=True)

    # Sticky summary bar
    render_sticky_summary(results)

    # Alert notifications
    if st.session_state.triggered_alerts:
        st.error(f"🚨 **{len(st.session_state.triggered_alerts)} Alert Rule(s) Triggered!**")
        for alert in st.session_state.triggered_alerts:
            rule = alert['rule']
            st.warning(
                f"⚠️ Rule triggered: **{rule['severity']}** errors "
                f"in **{rule['component'] or 'any component'}** "
                f"({alert['count']} occurrences) → Action: {rule['action']}"
            )
        st.markdown("---")

    # Executive Summary
    st.header("📋 Executive Summary")

    if results['requires_immediate_attention']:
        st.error(f"🔴 **CRITICAL - Immediate Action Required!**\n\n{results['final_summary']}")
    else:
        st.success(f"🟢 **System Status: Normal**\n\n{results['final_summary']}")

    st.markdown("---")

    # Clean Key Metrics
    st.header("📊 Key Metrics")

    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📄 Total Logs", f"{results['total_logs']:,}")
    
    with col2:
        suspicious_pct = (len(results['suspicious_indices']) / results['total_logs'] * 100) if results['total_logs'] > 0 else 0
        st.metric("⚠️ Suspicious", len(results['suspicious_indices']), f"{suspicious_pct:.1f}%")
    
    with col3:
        st.metric("❌ Confirmed Errors", len(results['error_events']))
    
    with col4:
        critical_count = len([e for e in results['error_events'] if e.get('severity') == 'CRITICAL'])
        st.metric("🔴 Critical", critical_count, "Urgent!" if critical_count > 0 else None, delta_color="inverse")

    # Second row
    col5, col6, col7 = st.columns(3)
    
    with col5:
        high_count = len([e for e in results['error_events'] if e.get('severity') == 'HIGH'])
        st.metric("🟠 High Priority", high_count)
    
    with col6:
        cache_efficiency = (results.get('cache_hits', 0) / results['total_logs'] * 100) if results['total_logs'] > 0 else 0
        st.metric("⚡ Cache Efficiency", f"{cache_efficiency:.1f}%")
    
    with col7:
        st.metric("⏱️ Processing Time", f"{results.get('processing_time', 0):.1f}s")

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📈 Timeline",
        "🔍 Error Analysis",
        "🔗 Related Errors",
        "🏥 Component Health",
        "📊 Visualizations",
        "💡 Recommendations",
        "💾 Export"
    ])

    # ========================================================================
    # TAB 1: ENHANCED TIMELINE
    # ========================================================================

    with tab1:
        st.header("📈 Error Timeline")

        timeline_data = st.session_state.timeline_data

        if timeline_data and timeline_data.get('has_timestamps'):
            # Error storms
            if timeline_data.get('error_storms'):
                st.markdown(f"""
                <div class="timeline-card-warning">
                    <h3>⚡ {len(timeline_data['error_storms'])} Error Storm(s) Detected!</h3>
                    <p>Sudden spike in error frequency detected</p>
                </div>
                """, unsafe_allow_html=True)
                
                for storm in timeline_data['error_storms']:
                    st.error(f"🌩️ Storm at **{storm['time']}** - {storm['count']} errors")

            # Enhanced timeline chart
            time_buckets = timeline_data.get('time_buckets', {})
            if time_buckets:
                df_timeline = pd.DataFrame(
                    list(time_buckets.items()),
                    columns=['Time', 'Error Count']
                )

                # Create interactive plotly chart
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=df_timeline['Time'],
                    y=df_timeline['Error Count'],
                    mode='lines+markers',
                    name='Errors',
                    line=dict(color='#667eea', width=3),
                    marker=dict(size=8, color='#764ba2'),
                    fill='tozeroy',
                    fillcolor='rgba(102, 126, 234, 0.2)',
                    hovertemplate='<b>Time:</b> %{x}<br><b>Errors:</b> %{y}<extra></extra>'
                ))
                
                fig.update_layout(
                    title="Error Frequency Over Time (Hover for details)",
                    xaxis_title="Time",
                    yaxis_title="Number of Errors",
                    xaxis_tickangle=-45,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    hovermode='x unified',
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)

            # Timeline stats - cleaner version
            st.markdown("### ⏰ Timeline Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                start_time_str = timeline_data.get('start_time', 'Unknown')
                if start_time_str != 'Unknown':
                    try:
                        dt = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                        start_display = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        start_display = start_time_str[:19]
                else:
                    start_display = 'Unknown'
                st.info(f"**📅 Start Time**\n\n{start_display}")
                
            with col2:
                end_time_str = timeline_data.get('end_time', 'Unknown')
                if end_time_str != 'Unknown':
                    try:
                        dt = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
                        end_display = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        end_display = end_time_str[:19]
                else:
                    end_display = 'Unknown'
                st.info(f"**📅 End Time**\n\n{end_display}")
            
            with col3:
                peak_time_str = timeline_data.get('peak_time', 'Unknown')
                if peak_time_str != 'Unknown':
                    try:
                        if 'T' in peak_time_str or len(peak_time_str) > 16:
                            dt = datetime.fromisoformat(peak_time_str.replace('Z', '+00:00'))
                            peak_display = dt.strftime('%Y-%m-%d %H:%M')
                        else:
                            peak_display = peak_time_str
                    except:
                        peak_display = peak_time_str
                else:
                    peak_display = 'Unknown'
                st.warning(f"**⚡ Peak Time**\n\n{peak_display}")
                
            with col4:
                peak_count = timeline_data.get('peak_count', 0)
                st.warning(f"**📊 Peak Count**\n\n{peak_count} errors")
            
            # Duration
            duration_seconds = timeline_data.get('duration_seconds', 0)
            if duration_seconds > 0:
                hours = int(duration_seconds // 3600)
                minutes = int((duration_seconds % 3600) // 60)
                seconds = int(duration_seconds % 60)
                
                if hours > 0:
                    duration_display = f"{hours}h {minutes}m {seconds}s"
                elif minutes > 0:
                    duration_display = f"{minutes}m {seconds}s"
                else:
                    duration_display = f"{seconds}s"
                    
                st.success(f"**⏱️ Total Duration:** {duration_display}")

        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-emoji">⏰</div>
                <h3>No Timestamps Found</h3>
                <p>Timeline analysis requires timestamped log entries</p>
                <p style="color: #667eea;">Expected format: <code>2026-02-11 10:15:32 ERROR [Component] Message</code></p>
            </div>
            """, unsafe_allow_html=True)

    # ========================================================================
    # TAB 2: ENHANCED ERROR ANALYSIS
    # ========================================================================

    with tab2:
        st.header("🔍 Detailed Error Analysis")

        # Enhanced filters
        st.subheader("🎛️ Filters")
        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

        with filter_col1:
            severity_filter = st.multiselect(
                "⚠️ Severity",
                options=['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'],
                default=['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']
            )

        with filter_col2:
            categories = list(set([e.get('category', 'GENERIC') for e in results['error_events']]))
            category_filter = st.multiselect(
                "🏷️ Category",
                options=categories,
                default=categories
            )

        with filter_col3:
            min_confidence = st.slider("🎯 Min Confidence", 0, 100, 0)

        with filter_col4:
            search_query = st.text_input("🔎 Search", placeholder="Search errors...")

        components = list(set([e.get('component', 'Unknown') for e in results['error_events']]))
        component_filter = st.multiselect(
            "🔧 Component Filter",
            options=components,
            default=components
        )

        view_mode = st.radio(
            "View Mode",
            ["Grouped (Deduplicated)", "Individual Errors"],
            horizontal=True
        )

        # Apply filters
        filtered_errors = [
            e for e in results['error_events']
            if e.get('severity', 'INFO') in severity_filter
            and e.get('category', 'GENERIC') in category_filter
            and (e.get('confidence', 0) * 100) >= min_confidence
            and e.get('component', 'Unknown') in component_filter
            and (not search_query or
                 search_query.lower() in e.get('message', '').lower() or
                 search_query.lower() in e.get('exception_class', '').lower() or
                 search_query.lower() in e.get('component', '').lower())
        ]

        st.info(f"📋 Showing **{len(filtered_errors)}** of **{len(results['error_events'])}** errors")

        # Render errors with enhanced cards
        if view_mode == "Grouped (Deduplicated)" and st.session_state.grouped_errors:
            grouper = ErrorGrouper()
            filtered_groups = grouper.create_grouped_summary(filtered_errors)

            if not st.session_state.view_mode_compact:
                # Full view with enhanced cards
                for group in filtered_groups:
                    rep_error = group['representative_error']
                    severity = rep_error.get('severity', 'INFO')
                    
                    # Get first root cause and action for preview
                    quick_fix = rep_error.get('recommended_actions', ['Investigate'])[0] if rep_error.get('recommended_actions') else 'Investigate'
                    root_cause = rep_error.get('possible_root_causes', ['Unknown'])[0] if rep_error.get('possible_root_causes') else 'Unknown'

                    with st.expander(
                        f"{get_severity_emoji(severity)} **{rep_error.get('exception_class', 'Unknown')}** | "
                        f"{rep_error.get('component', 'Unknown')} | "
                        f"Occurred **{group['occurrences']}x** {render_occurrence_dots(group['occurrences'])} | {severity}",
                        expanded=(severity in ['CRITICAL', 'HIGH'] and group['occurrences'] >= 5)
                    ):
                        # Enhanced error card with preview
                        error_card_html = f"""
                        <div class="error-card error-card-{severity.lower()}">
                            <div class="error-preview">
                                <div class="error-quick-fix">💡 Quick Fix: {quick_fix}</div>
                                <div class="error-impact">⚠️ Root Cause: {root_cause}</div>
                            </div>
                        </div>
                        """
                        st.markdown(error_card_html, unsafe_allow_html=True)

                        col_a, col_b = st.columns([2, 1])

                        with col_a:
                            st.markdown(f"### {get_category_icon(rep_error.get('category', 'GENERIC'))} Error Details")
                            st.write(f"**Exception:** {rep_error.get('exception_class', 'Unknown')}")
                            st.write(f"**Component:** {rep_error.get('component', 'Unknown')}")
                            st.write(f"**Category:** {rep_error.get('category', 'GENERIC')}")

                            if rep_error.get('severity_adjusted'):
                                st.warning(f"⚡ Severity auto-adjusted: {rep_error.get('original_severity')} → {severity} (occurs {group['occurrences']}x)")

                            if rep_error.get('message'):
                                st.markdown("**Message:**")
                                highlighted_msg = highlight_search_text(rep_error['message'], search_query)
                                st.markdown(f'<div style="background: rgba(102, 126, 234, 0.1); padding: 12px; border-radius: 6px;">{highlighted_msg}</div>', unsafe_allow_html=True)

                        with col_b:
                            st.markdown("### 📊 Metrics")
                            st.metric("Occurrences", group['occurrences'])
                            st.metric("Severity", severity)
                            st.metric("Confidence", f"{rep_error.get('confidence', 0)*100:.0f}%")

                            if group['line_numbers']:
                                st.markdown(f"**Lines:** {', '.join(map(str, group['line_numbers'][:5]))}")
                                if len(group['line_numbers']) > 5:
                                    st.markdown(f"... and {len(group['line_numbers'])-5} more")

                        if group['first_seen'] or group['last_seen']:
                            st.markdown("### 🕐 Occurrence Timeline")
                            timeline_col1, timeline_col2 = st.columns(2)
                            with timeline_col1:
                                if group['first_seen']:
                                    st.info(f"**First seen:** {group['first_seen']}")
                            with timeline_col2:
                                if group['last_seen']:
                                    st.info(f"**Last seen:** {group['last_seen']}")

                        if rep_error.get('line_number'):
                            st.markdown("### 📍 Error Location & Context")
                            render_context_viewer(rep_error, search_query)

                        if rep_error.get('reasoning'):
                            st.markdown("### 💭 Analysis Reasoning")
                            st.warning(rep_error['reasoning'])

                        if rep_error.get('possible_root_causes'):
                            st.markdown("### 🔍 Possible Root Causes")
                            for cause in rep_error['possible_root_causes']:
                                st.markdown(f"- {cause}")

                        if rep_error.get('recommended_actions'):
                            st.markdown("### 💡 Recommended Actions")
                            for action in rep_error['recommended_actions']:
                                st.success(f"✓ {action}")
            else:
                # Compact view
                for group in filtered_groups:
                    rep_error = group['representative_error']
                    severity = rep_error.get('severity', 'INFO')
                    color = get_severity_color(severity)
                    
                    compact_html = f"""
                    <div class="compact-error-item" style="border-left-color: {color};">
                        <span style="color: {color}; font-weight: bold;">{severity}</span>
                        <span style="margin: 0 8px;">|</span>
                        <span>{rep_error.get('exception_class', 'Unknown')}</span>
                        <span style="margin: 0 8px;">|</span>
                        <span>{rep_error.get('component', 'Unknown')}</span>
                        <span style="margin: 0 8px;">|</span>
                        <span style="color: #667eea;">{group['occurrences']}x</span>
                    </div>
                    """
                    st.markdown(compact_html, unsafe_allow_html=True)

        else:
            # Individual errors view
            if not filtered_errors:
                st.markdown("""
                <div class="empty-state">
                    <div class="empty-state-emoji">🎉</div>
                    <h3>No Errors Match Your Filters</h3>
                    <p>Try adjusting your filter criteria</p>
                </div>
                """, unsafe_allow_html=True)
            
            for i, error in enumerate(filtered_errors):
                severity = error.get('severity', 'INFO')
                quick_fix = error.get('recommended_actions', ['Investigate'])[0] if error.get('recommended_actions') else 'Investigate'
                
                with st.expander(
                    f"{get_severity_emoji(severity)} **#{i+1}** - "
                    f"{error.get('exception_class', 'Unknown')} | "
                    f"{error.get('component', 'Unknown')} | {severity} | "
                    f"Confidence: {error.get('confidence', 0)*100:.0f}%",
                    expanded=(i < 3)
                ):
                    error_card_html = f"""
                    <div class="error-card error-card-{severity.lower()}">
                        <div class="error-preview">
                            <div class="error-quick-fix">💡 Quick Fix: {quick_fix}</div>
                        </div>
                    </div>
                    """
                    st.markdown(error_card_html, unsafe_allow_html=True)

                    col_a, col_b = st.columns([2, 1])

                    with col_a:
                        st.markdown(f"### {get_category_icon(error.get('category', 'GENERIC'))} Error Details")
                        st.write(f"**Exception:** {error.get('exception_class', 'Unknown')}")
                        st.write(f"**Component:** {error.get('component', 'Unknown')}")
                        st.write(f"**Category:** {error.get('category', 'GENERIC')}")

                        if error.get('severity_adjusted'):
                            st.warning(f"⚡ Severity auto-adjusted from {error.get('original_severity')} to {severity}")

                        if error.get('message'):
                            st.markdown("**Message:**")
                            highlighted_msg = highlight_search_text(error['message'], search_query)
                            st.markdown(f'<div style="background: rgba(102, 126, 234, 0.1); padding: 12px; border-radius: 6px;">{highlighted_msg}</div>', unsafe_allow_html=True)

                    with col_b:
                        st.markdown("### 📊 Metrics")
                        st.metric("Severity", severity)
                        st.metric("Confidence", f"{error.get('confidence', 0)*100:.0f}%")
                        if error.get('stack_trace_depth'):
                            st.metric("Stack Depth", f"{error['stack_trace_depth']} frames")

                    st.markdown("### 📍 Error Location & Context")
                    render_context_viewer(error, search_query)

                    if error.get('reasoning'):
                        st.markdown("### 💭 Analysis Reasoning")
                        st.warning(error['reasoning'])

                    if error.get('possible_root_causes'):
                        st.markdown("### 🔍 Possible Root Causes")
                        for cause in error['possible_root_causes']:
                            st.markdown(f"- {cause}")

                    if error.get('recommended_actions'):
                        st.markdown("### 💡 Recommended Actions")
                        for action in error['recommended_actions']:
                            st.success(f"✓ {action}")

                    if error.get('needs_review'):
                        st.warning("⚠️ Flagged for manual review (low confidence)")

    # ========================================================================
    # TAB 3: RELATED ERRORS
    # ========================================================================

    with tab3:
        st.header("🔗 Related Error Detection")

        suspicious_with_context = results.get('suspicious_with_context', [])

        if suspicious_with_context:
            from crysys_v3 import ContextExtractor
            ctx_extractor = ContextExtractor()
            chains = ctx_extractor.detect_related_errors(suspicious_with_context)

            if chains:
                st.markdown(f"""
                <div class="timeline-card-warning">
                    <h3>🔗 Found {len(chains)} Error Chain(s)</h3>
                    <p>These errors likely caused each other (occurred within 5 seconds)</p>
                </div>
                """, unsafe_allow_html=True)

                for i, chain in enumerate(chains):
                    with st.expander(f"🔗 Error Chain #{i+1} - {chain['count']} related errors", expanded=True):
                        st.markdown(f"**Time window:** {chain.get('start_time', 'Unknown')} → {chain.get('end_time', 'Unknown')}")
                        st.markdown(f"**Errors in chain:** {chain['count']}")

                        for j, ctx_error in enumerate(chain['errors']):
                            arrow = "🔴" if j == 0 else "↓ 🟠"
                            highlighted_line = highlight_search_text(ctx_error['log_line'][:150], "")
                            st.markdown(f"{arrow} **Line {ctx_error['line_number']}:** `{highlighted_line}`")
                            if ctx_error.get('timestamp'):
                                st.markdown(f"   ⏰ {ctx_error['timestamp']}")

                        st.info(f"💡 **Tip:** The first error (Line {chain['errors'][0]['line_number']}) is likely the ROOT CAUSE! Fix it first.")
            else:
                st.markdown("""
                <div class="empty-state">
                    <div class="empty-state-emoji">✅</div>
                    <h3>No Error Chains Detected</h3>
                    <p>Errors appear to be independent</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("ℹ️ No context data available")

    # ========================================================================
    # TAB 4: COMPONENT HEALTH
    # ========================================================================

    with tab4:
        render_component_health(results)

    # ========================================================================
    # TAB 5: ENHANCED VISUALIZATIONS
    # ========================================================================

    with tab5:
        st.header("📊 Interactive Visualizations")

        if results['error_events']:
            viz_tab1, viz_tab2, viz_tab3, viz_tab4 = st.tabs([
                "🥧 Severity", "📊 Categories", "🎯 Confidence", "🏷️ Components"
            ])

            with viz_tab1:
                severity_counts = defaultdict(int)
                for event in results['error_events']:
                    severity_counts[event.get('severity', 'INFO')] += 1

                fig = px.pie(
                    values=list(severity_counts.values()),
                    names=list(severity_counts.keys()),
                    title="Error Severity Distribution (Click to filter)",
                    color_discrete_map={
                        'CRITICAL': '#f56565',
                        'HIGH': '#ed8936',
                        'MEDIUM': '#ecc94b',
                        'LOW': '#48bb78',
                        'INFO': '#4299e1'
                    },
                    hole=0.3
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)

            with viz_tab2:
                category_counts = defaultdict(int)
                for event in results['error_events']:
                    category_counts[event.get('category', 'GENERIC')] += 1

                fig = px.bar(
                    x=list(category_counts.keys()),
                    y=list(category_counts.values()),
                    title="Errors by Category",
                    color=list(category_counts.values()),
                    color_continuous_scale='Purples',
                    text=list(category_counts.values())
                )
                fig.update_traces(texttemplate='%{text}', textposition='outside')
                st.plotly_chart(fig, use_container_width=True)

            with viz_tab3:
                confidences = [e.get('confidence', 0) * 100 for e in results['error_events']]
                fig = px.histogram(
                    confidences,
                    nbins=20,
                    title="Confidence Score Distribution",
                    color_discrete_sequence=['#667eea'],
                    labels={'value': 'Confidence (%)', 'count': 'Errors'}
                )
                st.plotly_chart(fig, use_container_width=True)

            with viz_tab4:
                component_counts = defaultdict(int)
                for event in results['error_events']:
                    component_counts[event.get('component', 'Unknown')] += 1

                fig = px.bar(
                    x=list(component_counts.values()),
                    y=list(component_counts.keys()),
                    orientation='h',
                    title="Errors by Component",
                    color=list(component_counts.values()),
                    color_continuous_scale='Reds',
                    text=list(component_counts.values())
                )
                fig.update_traces(texttemplate='%{text}', textposition='outside')
                st.plotly_chart(fig, use_container_width=True)

        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-emoji">📊</div>
                <h3>No Data to Visualize</h3>
                <p>No errors found in the analysis</p>
            </div>
            """, unsafe_allow_html=True)

    # ========================================================================
    # TAB 6: RECOMMENDATIONS
    # ========================================================================

    with tab6:
        st.header("💡 Automated Recommendations")

        if results.get('recommendations'):
            for i, rec in enumerate(results['recommendations'], 1):
                st.success(f"**{i}.** {rec}")

        st.markdown("---")
        st.subheader("🔧 Priority Action Items")

        action_items = []
        severity_errors = defaultdict(list)
        for error in results['error_events']:
            severity_errors[error.get('severity', 'INFO')].append(error)

        if severity_errors.get('CRITICAL'):
            for error in severity_errors['CRITICAL']:
                action_items.append({
                    'Priority': '🔴 P0 - Immediate',
                    'Component': error.get('component', 'Unknown'),
                    'Action': error.get('recommended_actions', ['Investigate immediately'])[0]
                    if error.get('recommended_actions') else 'Investigate immediately',
                    'Issue': error.get('exception_class', 'Critical Error')
                })

        if severity_errors.get('HIGH'):
            for error in severity_errors['HIGH'][:3]:
                action_items.append({
                    'Priority': '🟠 P1 - Urgent',
                    'Component': error.get('component', 'Unknown'),
                    'Action': error.get('recommended_actions', ['Fix soon'])[0]
                    if error.get('recommended_actions') else 'Fix soon',
                    'Issue': error.get('exception_class', 'High Priority Error')
                })

        if action_items:
            df_actions = pd.DataFrame(action_items)
            st.dataframe(df_actions, use_container_width=True, hide_index=True)
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-emoji">🎉</div>
                <h3>No High-Priority Action Items</h3>
                <p>All errors are low priority</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("⚡ Performance Metrics")

        perf_col1, perf_col2, perf_col3, perf_col4 = st.columns(4)
        with perf_col1:
            st.info(f"**Processing Time**\n\n{results.get('processing_time', 0):.2f}s")
        with perf_col2:
            st.info(f"**Tokens Used**\n\n{results.get('tokens_used', 0):,}")
        with perf_col3:
            st.info(f"**Analysis Route**\n\n{results.get('route_taken', 'unknown').title()}")
        with perf_col4:
            speed = results['total_logs'] / max(results.get('processing_time', 1), 1)
            st.info(f"**Speed**\n\n{speed:.0f} logs/sec")

    # ========================================================================
    # TAB 7: EXPORT
    # ========================================================================

    with tab7:
        st.header("💾 Export Results")

        export_col1, export_col2, export_col3 = st.columns(3)

        with export_col1:
            json_data = json.dumps(results, indent=2, default=str)
            st.download_button(
                label="📥 Full Results (JSON)",
                data=json_data,
                file_name=f"crysys_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )

        with export_col2:
            if results['error_events']:
                flat_errors = []
                for e in results['error_events']:
                    flat_errors.append({
                        'exception_class': e.get('exception_class', ''),
                        'severity': e.get('severity', ''),
                        'component': e.get('component', ''),
                        'category': e.get('category', ''),
                        'message': e.get('message', ''),
                        'confidence': e.get('confidence', 0),
                        'line_number': e.get('line_number', ''),
                        'timestamp': e.get('timestamp', ''),
                        'reasoning': e.get('reasoning', ''),
                        'root_causes': ', '.join(e.get('possible_root_causes', [])),
                        'actions': ', '.join(e.get('recommended_actions', []))
                    })
                df = pd.DataFrame(flat_errors)
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="📥 Errors Table (CSV)",
                    data=csv_data,
                    file_name=f"crysys_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

        with export_col3:
            try:
                export_utils = ExportUtils()
                excel_data = export_utils.create_excel_export(results)
                st.download_button(
                    label="📥 Full Report (Excel)",
                    data=excel_data,
                    file_name=f"crysys_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            except Exception as e:
                st.warning(f"Excel export unavailable: {e}")

        st.markdown("---")
        st.subheader("📋 JIRA Ticket Format")

        if results['error_events']:
            critical_high = [e for e in results['error_events']
                           if e.get('severity') in ['CRITICAL', 'HIGH']]

            if critical_high:
                selected_error_idx = st.selectbox(
                    "Select error to format for JIRA",
                    range(len(critical_high)),
                    format_func=lambda i: f"{critical_high[i].get('exception_class', 'Unknown')} - {critical_high[i].get('component', 'Unknown')}"
                )

                selected_error = critical_high[selected_error_idx]
                export_utils = ExportUtils()
                jira_text = export_utils.create_jira_format(selected_error)

                st.code(jira_text, language='markdown')
                st.download_button(
                    "📥 Download JIRA Format",
                    data=jira_text,
                    file_name="jira_ticket.md",
                    mime="text/markdown"
                )

            st.markdown("---")
            st.subheader("💬 Slack Message Format")

            if critical_high:
                slack_error = critical_high[0]
                slack_text = export_utils.create_slack_format(slack_error)
                st.code(slack_text, language='text')
                st.download_button(
                    "📥 Download Slack Format",
                    data=slack_text,
                    file_name="slack_message.txt",
                    mime="text/plain"
                )

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #a0aec0;'>"
    "🔥 Powered by CRYSYS v3.0 Enhanced Edition | "
    "Built with LangGraph + Groq LLaMA 3.3 70B + Streamlit | "
    "All Visual Enhancements Implemented ✨"
    "</p>",
    unsafe_allow_html=True
)






#    python -m streamlit run streamlit_app.py
