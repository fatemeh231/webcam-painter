import os
from PIL import Image, ImageDraw, ImageFont


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tiff"}
PDF_EXTS = {".pdf"}
MAX_PDF_PAGES = 200


def load_file_as_images(path, max_size=(1300, 850)):
    """
    Returns a list of PIL RGB images — one per page.
    Images and unsupported formats return a single-element list.
    """
    ext = os.path.splitext(path)[1].lower()

    if ext in IMAGE_EXTS:
        img = Image.open(path).convert("RGB")
        img.thumbnail(max_size, Image.LANCZOS)
        return [img]

    if ext in PDF_EXTS:
        return _render_pdf_all_pages(path, max_size)

    img = _placeholder(os.path.basename(path), ext)
    img.thumbnail(max_size, Image.LANCZOS)
    return [img]


def _render_pdf_all_pages(path, max_size, zoom=2.0):
    import fitz
    doc = fitz.open(path)
    pages = []
    for i, page in enumerate(doc):
        if i >= MAX_PDF_PAGES:
            break
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img.thumbnail(max_size, Image.LANCZOS)
        pages.append(img)
    doc.close()
    return pages


def _placeholder(name, ext):
    img = Image.new("RGB", (1000, 700), (245, 245, 245))
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, 980, 680], outline=(190, 190, 190), width=3)

    try:
        title_font = ImageFont.truetype("arial.ttf", 32)
        body_font = ImageFont.truetype("arial.ttf", 20)
    except Exception:
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()

    draw.text((60, 60), f"{name}", fill=(50, 50, 50), font=title_font)
    draw.text((60, 130), f"Type: {ext}", fill=(80, 80, 80), font=body_font)
    draw.text(
        (60, 200),
        "Preview for this format is not supported yet.",
        fill=(140, 140, 140),
        font=body_font,
    )
    return img