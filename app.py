import streamlit as st
from pydub import AudioSegment
import io
import os
import tempfile

st.set_page_config(page_title="MP3 Editor", page_icon="🎵", layout="centered")
st.title("🎵 MP3 Song Editor")
st.caption("Trim, Fade, and Merge MP3 files")

# ─── Helpers ──────────────────────────────────────────────────────────────────
def load_audio(uploaded_file) -> AudioSegment:
    """Save upload to a real temp file, then load — most reliable method."""
    suffix = os.path.splitext(uploaded_file.name)[-1]  # .mp3
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name
    audio = AudioSegment.from_file(tmp_path, format="mp3")
    os.remove(tmp_path)
    return audio

def export_as_wav(audio: AudioSegment) -> bytes:
    """Export as WAV — no ffmpeg encoding needed, always works."""
    buf = io.BytesIO()
    audio.export(buf, format="wav")
    buf.seek(0)
    return buf.read()

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["✂️ Trim", "🎚️ Fade", "🔗 Merge"])

# ── TAB 1: TRIM ───────────────────────────────────────────────────────────────
with tab1:
    st.subheader("Trim MP3")
    file = st.file_uploader("Upload MP3", type=["mp3"], key="trim_file")

    if file:
        st.caption("▶ Original:")
        st.audio(file)
        file.seek(0)

        audio = load_audio(file)
        duration_sec = len(audio) / 1000
        st.info(f"⏱ Duration: {duration_sec:.1f} seconds")

        col1, col2 = st.columns(2)
        start = col1.number_input("Start (sec)", min_value=0.0,
                                  max_value=duration_sec, value=0.0, step=0.5)
        end = col2.number_input("End (sec)", min_value=0.0,
                                max_value=duration_sec, value=duration_sec, step=0.5)

        if st.button("✂️ Trim Now"):
            if start >= end:
                st.error("Start must be less than End.")
            else:
                trimmed = audio[int(start * 1000): int(end * 1000)]
                result = export_as_wav(trimmed)
                st.success(f"✅ Trimmed to {end - start:.1f} seconds!")
                st.caption("▶ Preview:")
                st.audio(result, format="audio/wav")
                st.download_button("⬇️ Download Trimmed (WAV)", result,
                                   file_name="trimmed.wav", mime="audio/wav")

# ── TAB 2: FADE ───────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Add Fade In / Fade Out")
    file2 = st.file_uploader("Upload MP3", type=["mp3"], key="fade_file")

    if file2:
        st.caption("▶ Original:")
        st.audio(file2)
        file2.seek(0)

        audio2 = load_audio(file2)
        duration_sec2 = len(audio2) / 1000
        st.info(f"⏱ Duration: {duration_sec2:.1f} seconds")

        col3, col4 = st.columns(2)
        fade_in_ms = col3.slider("Fade In (ms)", 0, 5000, 500, step=100)
        fade_out_ms = col4.slider("Fade Out (ms)", 0, 5000, 1000, step=100)

        if st.button("🎚️ Apply Fade"):
            faded = audio2.fade_in(fade_in_ms).fade_out(fade_out_ms)
            result2 = export_as_wav(faded)
            st.success("✅ Fades applied!")
            st.caption("▶ Preview:")
            st.audio(result2, format="audio/wav")
            st.download_button("⬇️ Download Faded (WAV)", result2,
                               file_name="faded.wav", mime="audio/wav")

# ── TAB 3: MERGE ──────────────────────────────────────────────────────────────
with tab3:
    st.subheader("Merge / Concatenate MP3 Files")
    files = st.file_uploader("Upload MP3 files (in order)", type=["mp3"],
                              accept_multiple_files=True, key="merge_files")

    if files:
        for f in files:
            st.caption(f"🎵 {f.name}")
            st.audio(f)
            f.seek(0)

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

            result3 = export_as_wav(combined)
            total = len(combined) / 1000
            st.success(f"✅ Merged {len(files)} files → {total:.1f} sec total!")
            st.caption("▶ Preview:")
            st.audio(result3, format="audio/wav")
            st.download_button("⬇️ Download Merged (WAV)", result3,
                               file_name="merged.wav", mime="audio/wav")
