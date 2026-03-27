import streamlit as st
from pydub import AudioSegment
import io
import os
import tempfile

st.set_page_config(page_title="MP3 Editor", page_icon="🎵", layout="centered")
st.title("🎵 MP3 Song Editor")
st.caption("Trim, Fade, and Merge MP3 files — powered by PyDub")

# ─── Helpers ──────────────────────────────────────────────────────────────────
def load_audio(uploaded_file) -> AudioSegment:
    # Must wrap in BytesIO — Streamlit UploadedFile isn't directly readable by pydub
    audio_bytes = io.BytesIO(uploaded_file.read())
    return AudioSegment.from_file(audio_bytes, format="mp3")

def export_audio(audio: AudioSegment) -> bytes:
    # Export to a real temp file — BytesIO alone is unreliable with ffmpeg
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp_path = tmp.name
    audio.export(tmp_path, format="mp3")
    with open(tmp_path, "rb") as f:
        result = f.read()
    os.remove(tmp_path)
    return result

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["✂️ Trim", "🎚️ Fade", "🔗 Merge"])

# ── TAB 1: TRIM ───────────────────────────────────────────────────────────────
with tab1:
    st.subheader("Trim MP3")
    file = st.file_uploader("Upload MP3", type=["mp3"], key="trim_file")

    if file:
        # Preview original
        st.caption("Original:")
        st.audio(file)
        file.seek(0)  # Reset after st.audio reads it

        audio = load_audio(file)
        duration_sec = len(audio) / 1000
        st.info(f"Duration: {duration_sec:.1f} seconds")

        col1, col2 = st.columns(2)
        start = col1.number_input("Start (sec)", min_value=0.0,
                                  max_value=duration_sec, value=0.0, step=0.5)
        end = col2.number_input("End (sec)", min_value=0.0,
                                max_value=duration_sec, value=duration_sec, step=0.5)

        if st.button("✂️ Trim Now"):
            if start >= end:
                st.error("Start must be less than End.")
            else:
                trimmed = audio[int(start * 1000) : int(end * 1000)]
                result = export_audio(trimmed)
                st.success(f"Trimmed to {(end - start):.1f} seconds!")
                st.caption("Preview trimmed audio:")
                st.audio(result, format="audio/mp3")
                st.download_button("⬇️ Download Trimmed MP3", result,
                                   file_name="trimmed.mp3", mime="audio/mp3")

# ── TAB 2: FADE ───────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Add Fade In / Fade Out")
    file2 = st.file_uploader("Upload MP3", type=["mp3"], key="fade_file")

    if file2:
        st.caption("Original:")
        st.audio(file2)
        file2.seek(0)

        audio2 = load_audio(file2)
        duration_sec2 = len(audio2) / 1000
        st.info(f"Duration: {duration_sec2:.1f} seconds")

        col3, col4 = st.columns(2)
        fade_in = col3.slider("Fade In (ms)", 0, 5000, 500, step=100)
        fade_out = col4.slider("Fade Out (ms)", 0, 5000, 1000, step=100)

        if st.button("🎚️ Apply Fade"):
            faded = audio2.fade_in(fade_in).fade_out(fade_out)
            result2 = export_audio(faded)
            st.success("Fades applied!")
            st.caption("Preview faded audio:")
            st.audio(result2, format="audio/mp3")
            st.download_button("⬇️ Download Faded MP3", result2,
                               file_name="faded.mp3", mime="audio/mp3")

# ── TAB 3: MERGE ──────────────────────────────────────────────────────────────
with tab3:
    st.subheader("Merge / Concatenate MP3 Files")
    files = st.file_uploader("Upload MP3 files (in order)", type=["mp3"],
                              accept_multiple_files=True, key="merge_files")

    if files:
        st.write(f"{len(files)} file(s) uploaded:")
        for f in files:
            st.caption(f"🎵 {f.name}")
            st.audio(f)
            f.seek(0)  # Reset after st.audio reads it

        gap_ms = st.slider("Gap between songs (ms)", 0, 3000, 0, step=100)

        if st.button("🔗 Merge All"):
            combined = AudioSegment.empty()
            silence = AudioSegment.silent(duration=gap_ms)
            for i, f in enumerate(files):
                f.seek(0)
                seg = load_audio(f)
                combined += seg
                if i < len(files) - 1:
                    combined += silence

            result3 = export_audio(combined)
            total = len(combined) / 1000
            st.success(f"Merged {len(files)} files → {total:.1f} seconds total!")
            st.caption("Preview merged audio:")
            st.audio(result3, format="audio/mp3")
            st.download_button("⬇️ Download Merged MP3", result3,
                               file_name="merged.mp3", mime="audio/mp3")
