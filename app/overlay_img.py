import tempfile
import os
import zipfile
from PIL import Image
import numpy as np
from io import BytesIO
import shutil
import streamlit as st


def convert_to_png(image):
    if image.format != 'PNG':
        png_image = image.convert('RGBA')
        output = BytesIO()
        png_image.save(output, format='PNG')
        return Image.open(output)
    return image


def apply_layer_mask(base_image, mask_image):
    if base_image.size != mask_image.size:
        mask_image = mask_image.resize(base_image.size, Image.LANCZOS)
    base = np.array(base_image)
    mask = np.array(mask_image.convert('L'))
    result = np.dstack((base[:, :, :3], mask))
    return Image.fromarray(result)


def overlay_images(base, overlay):
    base = base.convert('RGBA')
    overlay = overlay.convert('RGBA')
    new_base = Image.new('RGBA', base.size, (0, 0, 0, 0))
    new_base.paste(overlay, (0, 0))
    return Image.alpha_composite(base, new_base)


def process_makeup(xaela_makeup, raen_makeup, base_folder):
    with tempfile.TemporaryDirectory() as temp_dir:
        xaela_png = convert_to_png(Image.open(xaela_makeup))
        raen_png = convert_to_png(Image.open(raen_makeup))
        layer_mask = Image.open(os.path.join('app', 'layer_mask.png'))

        if np.array_equal(np.array(xaela_png), np.array(raen_png)):
            st.error("Error: Xaela and Raen textures are identical. Please tint your makeup to Raen.")
            return None

        if xaela_png.width == xaela_png.height:
            xaela_png = xaela_png.crop((0, 0, xaela_png.width // 2, xaela_png.height))
        xaela_png = apply_layer_mask(xaela_png, layer_mask)

        if raen_png.width == raen_png.height:
            raen_png = raen_png.crop((0, 0, raen_png.width // 2, raen_png.height))
        raen_png = apply_layer_mask(raen_png, layer_mask)

        # Step 1: Apply makeup to all subfolders in the base folder (for both Raen and Xaela)
        for race_folder in os.listdir(base_folder):
            race_path = os.path.join(base_folder, race_folder)
            if not os.path.isdir(race_path):
                continue

            is_raen = race_folder.lower() == "raen"

            for root, dirs, files in os.walk(race_path):
                for file in files:
                    if file.lower().endswith('.png'):
                        base_image_path = os.path.join(root, file)
                        try:
                            base_image = Image.open(base_image_path)

                            # Apply makeup
                            makeup = raen_png if is_raen else xaela_png
                            result = overlay_images(base_image, makeup)

                            # Save the result
                            output_path = os.path.join(temp_dir, os.path.relpath(root, base_folder), file)
                            os.makedirs(os.path.dirname(output_path), exist_ok=True)
                            result.save(output_path, format='PNG')
                        except Exception as e:
                            st.error(f"Error processing {base_image_path}: {str(e)}")

        # Step 2: Process additional overlays for Raen
        raen_folder = os.path.join(base_folder, 'raen')
        for root, dirs, files in os.walk(raen_folder):
            subfolder = os.path.basename(root)  # f1, f2, f3, or f4
            overlay_raen_folder = os.path.join("overlay_texture", 'raen', subfolder)

            if os.path.exists(overlay_raen_folder):
                for overlay_file in os.listdir(overlay_raen_folder):
                    if overlay_file.lower().endswith(('.png', '.dds', '.jpg', '.jpeg', '.bmp')):
                        base_image_path = os.path.join(temp_dir, os.path.relpath(root, base_folder),
                                                       "scaleless_vanilla.png")

                        # Duplicate base image
                        duplicate_path = os.path.join(temp_dir, os.path.relpath(root, base_folder), overlay_file)
                        shutil.copy2(base_image_path, duplicate_path)

                        # Overlay texture
                        overlay_image = Image.open(os.path.join(overlay_raen_folder, overlay_file))
                        final_result = overlay_images(Image.open(duplicate_path), overlay_image)
                        final_result.save(duplicate_path, format='PNG')

        # Step 3: Process additional overlays for Xaela
        xaela_folder = os.path.join(base_folder, 'xaela')
        for root, dirs, files in os.walk(xaela_folder):
            subfolder = os.path.basename(root)  # f1, f2, f3, or f4
            overlay_xaela_folder = os.path.join("overlay_texture", 'xaela', subfolder)

            if os.path.exists(overlay_xaela_folder):
                for overlay_file in os.listdir(overlay_xaela_folder):
                    if overlay_file.lower().endswith(('.png', '.dds', '.jpg', '.jpeg', '.bmp')):
                        base_image_path = os.path.join(temp_dir, os.path.relpath(root, base_folder),
                                                       "scaleless_vanilla.png")

                        # Duplicate base image
                        duplicate_path = os.path.join(temp_dir, os.path.relpath(root, base_folder), overlay_file)
                        shutil.copy2(base_image_path, duplicate_path)

                        # Overlay texture
                        overlay_image = Image.open(os.path.join(overlay_xaela_folder, overlay_file))
                        final_result = overlay_images(Image.open(duplicate_path), overlay_image)
                        final_result.save(duplicate_path, format='PNG')

        # Step 4: Delete scaleless_vanilla.png files
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file.lower() == "scaleless_vanilla.png":
                    os.remove(os.path.join(root, file))

        # Step 5: Create zip file
        zip_path = os.path.join(temp_dir, 'processed_textures.zip')
        with zipfile.ZipFile(zip_path, 'w') as zip_file:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    if file != 'processed_textures.zip':  # Exclude the zip file itself
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zip_file.write(file_path, arcname)

        with open(zip_path, 'rb') as f:
            return f.read()
