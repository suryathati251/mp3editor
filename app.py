import streamlit as st
from pydub import AudioSegment
import os, tempfile, shutil

# Explicitly set ffmpeg path for Streamlit Cloud
AudioSegment.converter = shutil.which("ffmpeg") or "/usr/bin/ffmpeg"
AudioSegment.ffmpeg    = shutil.which("ffmpeg") or "/usr/bin/ffmpeg"
AudioSegment.ffprobe   = shutil.which("ffprobe") or "/usr/bin/ffprobe"

st.set_page_config(page_title="MP3 Editor", page_icon="🎵", layout="centered")
st.title("🎵 MP3 Song Editor")
st.caption("Trim, Fade, Merge and Auto-Edit MP3 files — powered by PyDub")

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
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "✂️ Trim", "🎚️ Fade", "🔗 Merge", "🎛️ Mid Fade", "🎬 Auto Edit"
])

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
            min_value=0.0, max_value=duration_sec,
            value=0.0, step=1.0, format="%.1f"
        )
        end = col2.number_input(
            f"End (0 to {duration_sec})",
            min_value=0.0, max_value=duration_sec,
            value=duration_sec, step=1.0, format="%.1f"
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
    st.subheader("Fade In / Fade Out")
    st.caption("Applies fade at the very start and/or end of the song.")
    file2 = st.file_uploader("Upload MP3", type=["mp3"], key="fade_file")

    if file2:
        st.caption("▶ Original:")
        st.audio(file2)
        file2.seek(0)

        audio2 = load_audio(file2)
        duration_sec2 = round(len(audio2) / 1000, 2)
        st.info(f"⏱ Total Duration: **{duration_sec2} seconds**")

        col3, col4 = st.columns(2)
        fade_in_ms  = col3.slider("Fade In at Start (ms)", 0, 5000, 500, step=100)
        fade_out_ms = col4.slider("Fade Out at End (ms)", 0, 5000, 1000, step=100)

        st.write(f"🎯 Fade In: first **{fade_in_ms}ms** | "
                 f"Fade Out: last **{fade_out_ms}ms**")

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

# ── TAB 4: MID FADE ───────────────────────────────────────────────────────────
with tab4:
    st.subheader("🎛️ Fade at a Specific Position")
    st.caption("Creates a smooth volume dip anywhere in the middle of the song.")
    file4 = st.file_uploader("Upload MP3", type=["mp3"], key="pos_fade_file")

    if file4:
        st.caption("▶ Original:")
        st.audio(file4)
        file4.seek(0)

        audio4 = load_audio(file4)
        duration_sec4 = round(len(audio4) / 1000, 2)
        st.info(f"⏱ Total Duration: **{duration_sec4} seconds**")

        position = st.number_input(
            "📍 Fade position (sec) — center point of the dip",
            min_value=1.0, max_value=duration_sec4 - 1.0,
            value=round(duration_sec4 / 2, 1), step=1.0, format="%.1f"
        )
        fade_duration = st.slider(
            "⏱ Fade duration (ms) — total length of the dip",
            100, 3000, 1000, step=100
        )

        half_fade = fade_duration // 2
        dip_start = round(position - half_fade / 1000, 2)
        dip_end   = round(position + half_fade / 1000, 2)

        st.write(f"🎯 Volume will dip from **{dip_start}s** → **{position}s** "
                 f"→ **{dip_end}s** (total dip: **{fade_duration}ms**)")

        st.markdown(f"""
        ```
        Full song:   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        After fade:  ━━━━━━━━━━━━━━━━━▓▒░  ░▒▓━━━━━━━━━━━━━
                                      ↑       ↑
                                 {dip_start}s     {dip_end}s
        ```
        """)

        if st.button("🎛️ Apply Mid Fade"):
            pos_ms       = int(position * 1000)
            before       = audio4[:pos_ms]
            after        = audio4[pos_ms:]
            before_faded = before.fade_out(half_fade)
            after_faded  = after.fade_in(half_fade)
            combined4    = before_faded + after_faded

            with st.spinner("Applying mid fade..."):
                result4 = export_as_mp3(combined4)

            st.success(f"✅ Fade dip applied at {position}s!")
            st.caption("▶ Preview:")
            st.audio(result4, format="audio/mpeg")
            st.download_button("⬇️ Download Mid-Faded MP3", result4,
                               file_name="mid_faded.mp3", mime="audio/mpeg")

# ── TAB 5: AUTO EDIT ──────────────────────────────────────────────────────────
with tab5:
    st.subheader("🎬 Auto Edit — Trim Parts, Fade & Merge in One Go")
    st.caption("Upload one MP3, define multiple segments, apply fades on each, and merge into one final file.")

    file5 = st.file_uploader("Upload MP3", type=["mp3"], key="auto_edit_file")

    if file5:
        st.caption("▶ Original:")
        st.audio(file5)
        file5.seek(0)

        audio5 = load_audio(file5)
        duration_sec5 = round(len(audio5) / 1000, 2)
        st.info(f"⏱ Total Duration: **{duration_sec5} seconds**")

        st.markdown("---")
        st.markdown("### Step 1 — Define Segments to Keep")
        st.caption("Add as many segments as you want. They will be merged in order.")

        num_segments = st.number_input("How many segments?",
                                       min_value=1, max_value=10,
                                       value=2, step=1)

        segments = []
        for i in range(int(num_segments)):
            st.markdown(f"**Segment {i + 1}**")
            c1, c2, c3, c4 = st.columns(4)
            seg_start = c1.number_input(
                "Start (s)", min_value=0.0, max_value=duration_sec5,
                value=0.0, step=1.0, format="%.1f",
                key=f"seg_start_{i}"
            )
            seg_end = c2.number_input(
                "End (s)", min_value=0.0, max_value=duration_sec5,
                value=min(duration_sec5, 30.0), step=1.0, format="%.1f",
                key=f"seg_end_{i}"
            )
            seg_fade_in = c3.number_input(
                "Fade In (ms)", min_value=0, max_value=3000,
                value=500, step=100,
                key=f"seg_fadein_{i}"
            )
            seg_fade_out = c4.number_input(
                "Fade Out (ms)", min_value=0, max_value=3000,
                value=500, step=100,
                key=f"seg_fadeout_{i}"
            )
            segments.append((seg_start, seg_end, seg_fade_in, seg_fade_out))

        st.markdown("---")
        st.markdown("### Step 2 — Gap Between Segments")
        auto_gap_ms = st.slider("Gap between segments (ms)", 0, 3000, 0, step=100)

        st.markdown("---")
        st.markdown("### Step 3 — Preview & Download")

        # Live summary table
        st.markdown("**Your edit plan:**")
        summary_rows = ""
        for i, (ss, se, fi, fo) in enumerate(segments):
            duration = round(se - ss, 1)
            summary_rows += (f"| Segment {i+1} | {ss}s | {se}s | "
                             f"{duration}s | {fi}ms | {fo}ms |\n")

        st.markdown(
            "| Segment | Start | End | Duration | Fade In | Fade Out |\n"
            "|---|---|---|---|---|---|\n"
            + summary_rows
        )

        if st.button("🎬 Build Final MP3"):
            errors = []
            for i, (ss, se, fi, fo) in enumerate(segments):
                if ss >= se:
                    errors.append(f"Segment {i+1}: Start must be less than End.")
                elif (se - ss) < 0.5:
                    errors.append(f"Segment {i+1}: Too short — minimum 0.5 seconds.")

            if errors:
                for e in errors:
                    st.error(f"❌ {e}")
            else:
                with st.spinner("Building your final MP3..."):
                    final = AudioSegment.empty()
                    silence_gap = AudioSegment.silent(duration=auto_gap_ms)

                    for i, (ss, se, fi, fo) in enumerate(segments):
                        chunk = audio5[int(ss * 1000): int(se * 1000)]
                        if fi > 0:
                            chunk = chunk.fade_in(fi)
                        if fo > 0:
                            chunk = chunk.fade_out(fo)
                        final += chunk
                        if i < len(segments) - 1:
                            final += silence_gap

                    result5 = export_as_mp3(final)

                total5 = round(len(final) / 1000, 1)
                st.success(f"✅ Final MP3 built! "
                           f"{len(segments)} segments → {total5} seconds total")
                st.caption("▶ Preview Final:")
                st.audio(result5, format="audio/mpeg")
                st.download_button("⬇️ Download Final MP3", result5,
                                   file_name="final_edit.mp3", mime="audio/mpeg")
