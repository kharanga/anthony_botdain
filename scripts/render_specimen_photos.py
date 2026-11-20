from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

SPECIMEN_PHOTOS_DIR = Path(__file__).resolve().parent.parent / "specimens" / "photos"
FONT_CANDIDATES = [
    Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
]
FONT_SIZE = 40
LINE_HEIGHT = 64
MARGIN = 60
PAGE_WIDTH = 1000

SPECIMEN_MENU_LINES = [
    "SODA LA ESPECIMEN",
    "Gallo pinto con huevo  ₡2.500",
    "Arroz con camarones  ₡6.000",
    "Ceviche de pescado  ₡4.500",
    "Plátanos maduros  ₡1.500",
    "Café con leche  ₡1.200",
    "Jugo de piña  ₡1.800",
]

SPECIMEN_RECEIPT_LINES = [
    "SUPER ESPECIMEN S.A.",
    "Factura 000123",
    "Leche 1L  1.150",
    "Pan cuadrado  1.600",
    "TOTAL  2.750",
]

SPECIMEN_SEAFOOD_MENU_LINES = [
    "MARISCOS DE LA CASA",
    "Sopa de camarón  ₡5.500",
    "CEVICHE MIXTO  ₡4.800",
    "Langostinos al ajillo  ₡9.000",
    "Arroz con jaiba  ₡6.500",
    "Pescado entero frito  ₡7.000",
    "Casado con pollo  ₡3.800",
]

PHONE_PHOTO_TILT_DEGREES = 1.5
PHONE_PHOTO_BLUR_RADIUS = 1.2
PHONE_PHOTO_SCALE = 0.6
PHONE_PHOTO_INK = 70
PHONE_PHOTO_PAPER = 215


def first_available_font() -> ImageFont.FreeTypeFont:
    font_path = next(candidate for candidate in FONT_CANDIDATES if candidate.exists())
    return ImageFont.truetype(str(font_path), FONT_SIZE)


def rendered_page(lines: list[str]) -> Image.Image:
    page_height = MARGIN * 2 + LINE_HEIGHT * len(lines)
    page = Image.new("L", (PAGE_WIDTH, page_height), color=255)
    drawing = ImageDraw.Draw(page)
    font = first_available_font()
    for line_index, line_text in enumerate(lines):
        drawing.text((MARGIN, MARGIN + line_index * LINE_HEIGHT), line_text, fill=0, font=font)
    return page


def phone_photo_like(page: Image.Image) -> Image.Image:
    low_contrast = page.point(lambda value: PHONE_PHOTO_INK if value < 128 else PHONE_PHOTO_PAPER)
    tilted = low_contrast.rotate(PHONE_PHOTO_TILT_DEGREES, expand=True, fillcolor=PHONE_PHOTO_PAPER)
    blurred = tilted.filter(ImageFilter.GaussianBlur(PHONE_PHOTO_BLUR_RADIUS))
    smaller_size = (round(blurred.width * PHONE_PHOTO_SCALE), round(blurred.height * PHONE_PHOTO_SCALE))
    return blurred.resize(smaller_size, Image.Resampling.BILINEAR)


def save_with_transcription(page: Image.Image, lines: list[str], stem: str) -> None:
    page.save(SPECIMEN_PHOTOS_DIR / f"{stem}.png")
    (SPECIMEN_PHOTOS_DIR / f"{stem}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def render_specimen_photos() -> None:
    SPECIMEN_PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
    save_with_transcription(rendered_page(SPECIMEN_MENU_LINES), SPECIMEN_MENU_LINES, "specimen-menu")
    save_with_transcription(rendered_page(SPECIMEN_RECEIPT_LINES), SPECIMEN_RECEIPT_LINES, "specimen-receipt")
    save_with_transcription(
        phone_photo_like(rendered_page(SPECIMEN_SEAFOOD_MENU_LINES)), SPECIMEN_SEAFOOD_MENU_LINES, "specimen-seafood-menu"
    )


if __name__ == "__main__":
    render_specimen_photos()
