from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

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


def render_specimen_photos() -> None:
    SPECIMEN_PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
    rendered_page(SPECIMEN_MENU_LINES).save(SPECIMEN_PHOTOS_DIR / "specimen-menu.png")
    rendered_page(SPECIMEN_RECEIPT_LINES).save(SPECIMEN_PHOTOS_DIR / "specimen-receipt.png")


if __name__ == "__main__":
    render_specimen_photos()
