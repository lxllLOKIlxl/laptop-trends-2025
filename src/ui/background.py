"""
Компонент для фонового анімаційного градієнта / хвиль / частинок.
Виклик: render_background(kind='gradient', enabled=True)
kind: 'gradient' | 'waves' | 'particles'
"""
import streamlit as st
import streamlit.components.v1 as components

def _gradient_html():
    return """
    <style>
    .bg-animated {
      position: fixed;
      inset: 0;
      z-index: -1;
      pointer-events: none;
      background: linear-gradient(120deg, #00e6ff, #7c5cff, #00ff9c);
      background-size: 600% 600%;
      filter: blur(36px) saturate(120%);
      opacity: 0.22;
      animation: bgGradient 20s ease infinite;
    }
    @keyframes bgGradient {
      0% { background-position: 0% 50%; }
      50% { background-position: 100% 50%; }
      100% { background-position: 0% 50%; }
    }
    </style>
    <div class="bg-animated"></div>
    """

def _waves_html():
    return """
    <style>
    .bg-waves { position: fixed; left:0; right:0; bottom:0; height:28vh; z-index:-1; opacity:0.34; pointer-events:none; }
    .wave path { transform-origin: 50% 50%; animation: waveMove 8s linear infinite; }
    @keyframes waveMove { 0%{transform:translateX(0)}50%{transform:translateX(-8%)}100%{transform:translateX(0)} }
    </style>
    <div class="bg-waves">
      <svg class="wave" viewBox="0 0 1440 320" preserveAspectRatio="none" width="100%" height="100%">
        <defs>
          <linearGradient id="g1" x1="0" x2="1">
            <stop offset="0" stop-color="#00e6ff" stop-opacity="0.85"/>
            <stop offset="1" stop-color="#7c5cff" stop-opacity="0.85"/>
          </linearGradient>
        </defs>
        <path fill="url(#g1)" d="M0,64L48,96C96,128,192,192,288,218.7C384,245,480,235,576,213.3C672,192,768,160,864,144C960,128,1056,128,1152,149.3C1248,171,1344,213,1392,234.7L1440,256L1440,320L0,320Z"></path>
      </svg>
    </div>
    """

def _particles_html():
    # uses tsParticles CDN, pointer-events:none so не заважає клікам
    return """
    <div id="tsparticles" style="position:fixed; inset:0; z-index:-2; pointer-events:none;"></div>
    <script src="https://cdn.jsdelivr.net/npm/tsparticles@2/tsparticles.min.js"></script>
    <script>
    if (window && window.tsParticles) {
      tsParticles.load('tsparticles', {
        fpsLimit: 60,
        background: { color: { value: "transparent" } },
        particles: {
          number: { value: 40 },
          color: { value: ["#00e6ff", "#7c5cff", "#00ff9c"] },
          shape: { type: "circle" },
          opacity: { value: 0.32 },
          size: { value: { min: 2, max: 6 } },
          move: { enable: true, speed: 0.6, outModes: "bounce" }
        },
        interactivity: { detectsOn: "window", events: { onHover: { enable: false } } }
      });
    }
    </script>
    """

def render_background(kind: str = "gradient", enabled: bool = True):
    """
    Відображає фон. Викликай у app.py перед рендером основного контенту.
    kind: 'gradient' | 'waves' | 'particles'
    enabled: bool
    """
    if not enabled:
        return

    if kind == "gradient":
        st.markdown(_gradient_html(), unsafe_allow_html=True)
    elif kind == "waves":
        st.markdown(_waves_html(), unsafe_allow_html=True)
    elif kind == "particles":
        # use components.html to safely inject JS
        components.html(_particles_html(), height=0)
    else:
        # fallback to gradient
        st.markdown(_gradient_html(), unsafe_allow_html=True)
