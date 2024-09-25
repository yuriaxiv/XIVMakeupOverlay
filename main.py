import os
import streamlit as st

from app.overlay_img import process_makeup

st.title("Au Ra Overlay Program")

col1, col2 = st.columns(2)

raen_makeup = col1.file_uploader("Upload Raen makeup:",
                                 type=["png", "dds", "jpg", "jpeg", "bmp"])

xaela_makeup = col2.file_uploader("Upload Midlander/Xaela makeup:",
                                  type=["png", "dds", "jpg", "jpeg", "bmp"])

textures_only_btn = col1.button("Overlay Textures", key="textures")

if textures_only_btn and xaela_makeup and raen_makeup:
    base_folder = os.path.join("base_texture", "face", "diffuse")
    processed_zip = process_makeup(xaela_makeup, raen_makeup, base_folder)

    if processed_zip:
        st.download_button(
            label="Download Textures",
            data=processed_zip,
            file_name="textures.zip",
            mime="application/zip"
        )