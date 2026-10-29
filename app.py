"""CodeAlpha Task 1 - Language Translation Tool (Streamlit + Google Translate)."""
import io

import streamlit as st
from deep_translator import GoogleTranslator
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


def translate(text: str, source: str, target: str) -> str:
    # Google's free endpoint accepts ~5000 chars per request, so split long input.
    chunks = [text[i:i + 4500] for i in range(0, len(text), 4500)]
    return " ".join(GoogleTranslator(source=source, target=target).translate(c) for c in chunks)


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
            src = "auto" if src_name == "auto detect" else langs[src_name]
            with st.spinner("Translating..."):
                result = translate(text, src, langs[tgt_name])
            st.session_state["result"] = result
            st.session_state["tgt"] = langs[tgt_name]
        except Exception as e:
            st.error(f"Translation failed: {e}")

if "result" in st.session_state:
    st.subheader("Translation")
    # st.code shows a built-in copy button in the top-right corner
    st.code(st.session_state["result"], language=None, wrap_lines=True)

    if st.button("🔊 Listen"):
        try:
            audio = io.BytesIO()
            gTTS(st.session_state["result"], lang=st.session_state["tgt"].split("-")[0]).write_to_fp(audio)
            st.audio(audio.getvalue(), format="audio/mp3")
        except Exception as e:
            st.error(f"Text-to-speech isn't available for this language: {e}")
