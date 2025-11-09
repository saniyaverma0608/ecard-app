from PIL import Image

# --- Compatibility patch for Pillow >=10.0 ---
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

import streamlit as st
from moviepy.editor import ImageClip, TextClip, concatenate_videoclips, CompositeVideoClip, vfx
from PIL import Image, ImageEnhance, ImageDraw, ImageFont
import numpy as np
import tempfile, os, time

# -------------------------------------------------------------
# APP CONFIG
# -------------------------------------------------------------
st.set_page_config(page_title="💍 Wedding E-Card Creator", layout="centered")

st.title("💖 Wedding Invitation E-Card Creator")
st.write("Upload photos or text slides, customize, and create a beautiful animated e-card video.")

# -------------------------------------------------------------
# SESSION STATE INITIALIZATION
# -------------------------------------------------------------
if "slides" not in st.session_state:
    st.session_state.slides = []

# -------------------------------------------------------------
# ADD SLIDE OPTIONS
# -------------------------------------------------------------
st.sidebar.header("➕ Add New Slide")
add_option = st.sidebar.selectbox("Add a new slide type", ["Image Slide", "Text Slide"])

if add_option == "Image Slide":
    img_file = st.sidebar.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
    if img_file and st.sidebar.button("Add Image Slide"):
        st.session_state.slides.append({
            "type": "image",
            "file": img_file,
            "text": "",
            "duration": 4.0,
            "transition": 1.0
        })
        if hasattr(st, "rerun"):
            st.rerun()
        else:
            st.experimental_rerun()

elif add_option == "Text Slide":
    text_content = st.sidebar.text_area("Enter slide text")
    bg_color = st.sidebar.color_picker("Background color", "#fdf6f0")
    text_color = st.sidebar.color_picker("Text color", "#a52a2a")
    font_size = st.sidebar.slider("Font size", 30, 120, 60)
    if st.sidebar.button("Add Text Slide"):
        st.session_state.slides.append({
            "type": "text",
            "text": text_content,
            "bg_color": bg_color,
            "text_color": text_color,
            "font_size": font_size,
            "duration": 4.0,
            "transition": 1.0
        })
        if hasattr(st, "rerun"):
            st.rerun()
        else:
            st.experimental_rerun()

# -------------------------------------------------------------
# DISPLAY & EDIT SLIDES
# -------------------------------------------------------------
if st.session_state.slides:
    st.subheader("🖼️ Your Slides")
    for idx, slide in enumerate(st.session_state.slides):
        st.write(f"### Slide {idx+1}")

        cols = st.columns([3, 2, 1])

        with cols[0]:
            if slide["type"] == "image":
                st.image(slide["file"], use_column_width=True)
            else:
                st.markdown(
                    f"<div style='background-color:{slide['bg_color']};"
                    f"color:{slide['text_color']};padding:30px;font-size:{slide['font_size']}px;"
                    f"text-align:center;border-radius:12px;'>{slide['text']}</div>",
                    unsafe_allow_html=True
                )

        with cols[1]:
            st.write("**Edit Settings:**")
            slide["duration"] = st.slider(f"Duration (sec) for Slide {idx+1}", 2.0, 10.0, slide["duration"], 0.5, key=f"dur_{idx}")
            slide["transition"] = st.slider(f"Fade (sec)", 0.5, 3.0, slide["transition"], 0.1, key=f"fade_{idx}")

            if slide["type"] == "text":
                slide["text"] = st.text_area("Edit Text", slide["text"], key=f"text_{idx}")
                slide["bg_color"] = st.color_picker("Background Color", slide["bg_color"], key=f"bg_{idx}")
                slide["text_color"] = st.color_picker("Text Color", slide["text_color"], key=f"tc_{idx}")
                slide["font_size"] = st.slider("Font Size", 30, 120, slide["font_size"], key=f"fs_{idx}")

        with cols[2]:
            # reorder and delete buttons
            if st.button("Move Up", key=f"up_btn_{idx}") and idx > 0:
                st.session_state.slides[idx], st.session_state.slides[idx - 1] = (
                    st.session_state.slides[idx - 1],
                    st.session_state.slides[idx],
                )
                if hasattr(st, "rerun"):
                    st.rerun()
                else:
                    st.experimental_rerun()

            if st.button("Move Down", key=f"down_btn_{idx}") and idx < len(st.session_state.slides) - 1:
                st.session_state.slides[idx], st.session_state.slides[idx + 1] = (
                    st.session_state.slides[idx + 1],
                    st.session_state.slides[idx],
                )
                if hasattr(st, "rerun"):
                    st.rerun()
                else:
                    st.experimental_rerun()

            if st.button("Delete", key=f"del_{idx}"):
                st.session_state.slides.pop(idx)
                time.sleep(0.1)
                if hasattr(st, "rerun"):
                    st.rerun()
                else:
                    st.experimental_rerun()

# -------------------------------------------------------------
# CREATE FINAL VIDEO
# -------------------------------------------------------------
if st.session_state.slides:
    st.subheader("🎞️ Create Your E-Card Video")

    if st.button("✨ Generate E-Card Video"):
        with st.spinner("Creating your e-card video..."):
            with tempfile.TemporaryDirectory() as tmpdir:
                clips = []

                for idx, slide in enumerate(st.session_state.slides):
                    if slide["type"] == "image":
                        img = Image.open(slide["file"]).convert("RGB")
                        img = ImageEnhance.Brightness(img).enhance(1.05)
                        img = ImageEnhance.Contrast(img).enhance(1.1)
                        img = img.resize((1080, 1920))

                        img_path = os.path.join(tmpdir, f"slide_{idx}.jpg")
                        img.save(img_path)

                        base_clip = ImageClip(img_path).set_duration(slide["duration"])
                        base_clip = base_clip.resize(lambda t: 1 + 0.05 * t / slide["duration"])  # slight zoom-in
                        clip = base_clip.fx(vfx.fadein, slide["transition"]/2).fx(vfx.fadeout, slide["transition"]/2)

                    else:  # text slide
                        txt_clip = TextClip(
                            slide["text"],
                            fontsize=slide["font_size"],
                            color=slide["text_color"],
                            size=(1080, 1920),
                            bg_color=slide["bg_color"],
                            method='caption'
                        ).set_duration(slide["duration"])
                        clip = txt_clip.fx(vfx.fadein, slide["transition"]/2).fx(vfx.fadeout, slide["transition"]/2)

                    clips.append(clip)

                final = concatenate_videoclips(clips, method="compose")
                out_path = os.path.join(tmpdir, "wedding_ecard.mp4")
                final.write_videofile(out_path, fps=30, codec="libx264", audio_codec="aac")

                with open(out_path, "rb") as f:
                    st.download_button(
                        "⬇ Download Your E-Card Video",
                        data=f,
                        file_name="Wedding_ECard.mp4",
                        mime="video/mp4"
                    )

        st.success("✅ Your animated e-card video is ready!")

else:
    st.info("📤 Please add at least one slide (image or text) to create your e-card.")
