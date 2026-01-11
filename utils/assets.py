# utils/assets.py
import streamlit as st
import streamlit.components.v1 as components
import json

def play_sfx(sound_type: str):
    """Enregistre un son pour être joué au prochain rendu."""
    st.session_state.play_sound = sound_type

def show_confetti():
    """Déclenche une pluie de confettis via JS."""
    components.html("""
        <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
        <script>
            confetti({
                particleCount: 150,
                spread: 70,
                origin: { y: 0.6 },
                colors: ['#00dfd8', '#007cf0', '#ffffff']
            });
        </script>
    """, height=0)

def trigger_queued_sounds():
    """Génère et joue des sons de synthèse Clean Tech via Web Audio API."""
    if 'play_sound' in st.session_state and st.session_state.play_sound:
        sound_type = st.session_state.play_sound
        
        scripts = {
            "success": "playTone(660, 'sine', 0.1, 0.1, 0.4); playTone(880, 'sine', 0.1, 0.2, 0.4);",
            "error": "playTone(150, 'triangle', 0.3, 0.1, 0.5);",
            "click": "playTone(440, 'sine', 0.05, 0.05, 0.2);",
            "victory": "playTone(440, 'sine', 0.1, 0, 0.4); playTone(554, 'sine', 0.1, 0.1, 0.4); playTone(659, 'sine', 0.1, 0.2, 0.4); playTone(880, 'sine', 0.3, 0.3, 0.5);",
            "heal": "playTone(523, 'sine', 0.1, 0, 0.3); playTone(659, 'sine', 0.1, 0.1, 0.3); playTone(783, 'sine', 0.1, 0.2, 0.3); playTone(1046, 'sine', 0.2, 0.3, 0.4);",
            "alert": "playTone(220, 'square', 0.2, 0, 0.2); playTone(220, 'square', 0.2, 0.4, 0.2);",
            "save": "playTone(880, 'sine', 0.05, 0, 0.2); playTone(1320, 'sine', 0.05, 0.05, 0.2);",
            "levelup": "playTone(440, 'sawtooth', 0.1, 0, 0.2); playTone(880, 'sawtooth', 0.1, 0.1, 0.2); playTone(1760, 'sawtooth', 0.3, 0.2, 0.3);"
        }
        
        tone_script = scripts.get(sound_type, "")
        if tone_script:
            full_script = f"""
                <script>
                    function playTone(freq, type, duration, delay, vol) {{
                        var context = new (window.AudioContext || window.webkitAudioContext)();
                        var osc = context.createOscillator();
                        var gain = context.createGain();
                        osc.type = type;
                        osc.frequency.value = freq;
                        gain.gain.setValueAtTime(0, context.currentTime + delay);
                        gain.gain.linearRampToValueAtTime(vol, context.currentTime + delay + 0.01);
                        gain.gain.exponentialRampToValueAtTime(0.01, context.currentTime + delay + duration);
                        osc.connect(gain);
                        gain.connect(context.destination);
                        osc.start(context.currentTime + delay);
                        osc.stop(context.currentTime + delay + duration + 0.1);
                    }}
                    {tone_script}
                </script>
            """
            components.html(full_script, height=0)
        st.session_state.play_sound = None
