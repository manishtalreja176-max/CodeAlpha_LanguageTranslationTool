"""CodeAlpha Task 1 - Language Translation Tool (Streamlit).
Uses Google Translate first, and automatically falls back to MyMemory
if Google rate-limits the request (HTTP 429)."""
import io
import re
import time

import streamlit as st
from deep_translator import GoogleTranslator, MyMemoryTranslator
from gtts import gTTS

st.set_page_config(page_title="Language Translation Tool", page_icon="🌐")

FALLBACK = {
    "english": "en", "urdu": "ur", "hindi": "hi", "arabic": "ar", "french": "fr",
    "german": "de", "spanish": "es", "chinese (simplified)": "zh-CN",
    "japanese": "ja", "russian": "ru", "turkish": "tr", "italian": "it",
}


@st.cache_data(show_spinner=False)
def get_languages() -> dict:
    try:
        return GoogleTranslator().get_supported_languages(as_dict=True)
    except Exception:
        return FALLBACK


def split_text(text: str, limit: int) -> list:
    """Split on sentence boundaries into chunks no longer than `limit` characters."""
    chunks, cur = [], ""
    for s in re.split(r"(?<=[.!?])\s+", text.strip()):
        while len(s) > limit:                      # very long sentence
            if cur:
                chunks.append(cur); cur = ""
            chunks.append(s[:limit]); s = s[limit:]
        if len(cur) + len(s) + 1 > limit and cur:
            chunks.append(cur); cur = s
        else:
            cur = f"{cur} {s}".strip()
    if cur:
        chunks.append(cur)
    return chunks


def google_translate(text, src, tgt):
    out = []
    for chunk in split_text(text, 4500):
        for attempt in range(3):                   # retry with a growing delay
            try:
                out.append(GoogleTranslator(source=src, target=tgt).translate(chunk))
                break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(2 * (attempt + 1))
        time.sleep(0.3)
    return " ".join(out)


def mymemory_translate(text, src_name, tgt_name):
    mm = MyMemoryTranslator(source="english", target="german").get_supported_languages(as_dict=True)
    if tgt_name not in mm:
        raise ValueError(f"'{tgt_name}' not supported by backup service")
    src = "auto" if src_name == "auto detect" else mm.get(src_name)
    if src is None:
        raise ValueError(f"'{src_name}' not supported by backup service")
    out = []
    for chunk in split_text(text, 450):            # MyMemory limit is 500 chars
        out.append(MyMemoryTranslator(source=src, target=mm[tgt_name]).translate(chunk))
        time.sleep(0.3)
    return " ".join(out)


def translate(text, src_name, tgt_name, langs):
    src = "auto" if src_name == "auto detect" else langs[src_name]
    try:
        return google_translate(text, src, langs[tgt_name]), "Google Translate"
    except Exception as g_err:
        try:
            return mymemory_translate(text, src_name, tgt_name), "MyMemory (backup)"
        except Exception as m_err:
            raise RuntimeError(f"Google: {g_err}\n\nMyMemory: {m_err}")


st.title("🌐 Language Translation Tool")
langs = get_languages()
names = sorted(langs)

col1, col2 = st.columns(2)
src_name = col1.selectbox("From", ["auto detect"] + names, index=0)
tgt_name = col2.selectbox("To", names, index=names.index("urdu") if "urdu" in names else 0)

text = st.text_area("Enter text", height=160, placeholder="Type or paste text here...")

if st.button("Translate", type="primary"):
    if not text.strip():
        st.warning("Please enter some text first.")
    else:
        try:
            with st.spinner("Translating..."):
                result, engine = translate(text, src_name, tgt_name, langs)
            st.session_state.update(result=result, engine=engine, tgt=langs[tgt_name])
        except Exception as e:
            st.error("Both translation services are busy or blocked right now. "
                     "Wait a few minutes, or switch network (e.g. mobile hotspot), and try again.")
            st.caption(str(e))

if "result" in st.session_state:
    st.subheader("Translation")
    st.code(st.session_state["result"], language=None, wrap_lines=True)  # built-in copy button
    st.caption(f"Translated using {st.session_state['engine']}")

    if st.button("🔊 Listen"):
        try:
            audio = io.BytesIO()
            gTTS(st.session_state["result"], lang=st.session_state["tgt"].split("-")[0]).write_to_fp(audio)
            st.audio(audio.getvalue(), format="audio/mp3")
        except Exception as e:
            st.error(f"Text-to-speech isn't available right now: {e}")