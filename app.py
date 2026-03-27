import streamlit as st
from pydub import AudioSegment
import io, os, tempfile, shutil

# Explicitly set ffmpeg path for Streamlit Cloud
AudioSegment.converter = shutil.which("ffmpeg") or "/usr/bin/ffmpeg"
AudioSegment.ffmpeg    = shutil.which("ffmpeg") or "/usr/bin/ffmpeg"
AudioSegment.ffprobe   = shutil.which("ffprobe") or "/usr/bin/ffprobe"

st.set_page_config(page_title="MP3 Editor", page_icon="🎵", layout="centered")
st.title("🎵 MP3 Song Editor")
st.caption("Trim, Fade, and Merge MP3 files — powered by PyDub")

# ─── Helpers ──────────────────────────────────────────────────────────────────
def load_audio(uploaded_file) -> AudioSegment:
    suffix = os.path.splitext(uploaded_file.name)[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name
    audio = AudioSegment.from_file(tmp_path, format="mp3")
    os.remove(tmp_path)
    return audio

def export_as_mp3(audio: AudioSegment) -> bytes:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tmp_path = tmp.name
    audio.export(tmp_path, format="mp3", bitrate="192k")
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
        st.caption("▶ Original:")
        st.audio(file)
        file.seek(0)

        audio = load_audio(file)
        duration_sec = round(len(audio) / 1000, 2)
        st.info(f"⏱ Total Duration: **{duration_sec} seconds**")

        st.markdown("Set the trim range below (in seconds):")
        col1, col2 = st.columns(2)

        start = col1.number_input(
            f"Start (0 to {duration_sec})",
            min_value=0.0,
            max_value=duration_sec,
            value=0.0,
            step=1.0,
            format="%.1f"
        )
        end = col2.number_input(
            f"End (0 to {duration_sec})",
            min_value=0.0,
            max_value=duration_sec,
            value=duration_sec,
            step=1.0,
            format="%.1f"
        )

        st.write(f"🎯 Trimming from **{start}s** to **{end}s** "
                 f"→ **{round(end - start, 1)} seconds** kept")

        if st.button("✂️ Trim Now"):
            if start >= end:
                st.error("❌ Start must be less than End.")
            elif (end - start) < 0.5:
                st.error("❌ Trim range too small — pick at least 0.5 seconds.")
            else:
                with st.spinner("Trimming..."):
                    trimmed = audio[int(start * 1000): int(end * 1000)]
                    result = export_as_mp3(trimmed)
                st.success(f"✅ Trimmed to {round(end - start, 1)} seconds!")
                st.caption("▶ Preview:")
                st.audio(result, format="audio/mpeg")
                st.download_button("⬇️ Download Trimmed MP3", result,
                                   file_name="trimmed.mp3", mime="audio/mpeg")

# ── TAB 2: FADE ───────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Add Fade In / Fade Out")
    file2 = st.file_uploader("Upload MP3", type=["mp3"], key="fade_file")

    if file2:
        st.caption("▶ Original:")
        st.audio(file2)
        file2.seek(0)

        audio2 = load_audio(file2)
        duration_sec2 = round(len(audio2) / 1000, 2)
        st.info(f"⏱ Total Duration: **{duration_sec2} seconds**")

        col3, col4 = st.columns(2)
        fade_in_ms = col3.slider("Fade In (ms)", 0, 5000, 500, step=100)
        fade_out_ms = col4.slider("Fade Out (ms)", 0, 5000, 1000, step=100)

        if st.button("🎚️ Apply Fade"):
            with st.spinner("Applying fades..."):
                faded = audio2.fade_in(fade_in_ms).fade_out(fade_out_ms)
                result2 = export_as_mp3(faded)
            st.success("✅ Fades applied!")
            st.caption("▶ Preview:")
            st.audio(result2, format="audio/mpeg")
            st.download_button("⬇️ Download Faded MP3", result2,
                               file_name="faded.mp3", mime="audio/mpeg")

# ── TAB 3: MERGE ──────────────────────────────────────────────────────────────
with tab3:
    st.subheader("Merge / Concatenate MP3 Files")
    files = st.file_uploader("Upload MP3 files (in order)", type=["mp3"],
                              accept_multiple_files=True, key="merge_files")

    if files:
        st.write(f"**{len(files)} file(s) uploaded:**")
        for f in files:
            st.caption(f"🎵 {f.name}")
            st.audio(f)
            f.seek(0)

        gap_ms = st.slider("Gap between songs (ms)", 0, 3000, 0, step=100)

        if st.button("🔗 Merge All"):
            with st.spinner("Merging files..."):
                combined = AudioSegment.empty()
                silence = AudioSegment.silent(duration=gap_ms)
                for i, f in enumerate(files):
                    f.seek(0)
                    seg = load_audio(f)
                    combined += seg
                    if i < len(files) - 1:
                        combined += silence
                result3 = export_as_mp3(combined)

            total = round(len(combined) / 1000, 1)
            st.success(f"✅ Merged {len(files)} files → {total} seconds total!")
            st.caption("▶ Preview:")
            st.audio(result3, format="audio/mpeg")
            st.download_button("⬇️ Download Merged MP3", result3,
                               file_name="merged.mp3", mime="audio/mpeg")
