"""Генерация SVG/PNG логотипов без платных API."""

from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


STYLES = {
    "минимализм": "minimal",
    "яркий": "bold",
    "премиум": "premium",
    "дерзкий": "bold",
    "тёплый": "warm",
    "тепло": "warm",
    "техно": "tech",
}


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _initials(name: str) -> str:
    parts = [p for p in name.replace("-", " ").split() if p]
    if not parts:
        return "B"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[1][0]).upper()


def _font(size: int) -> ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def generate_logo(
    brand_name: str,
    palette: list[str],
    style: str,
    out_path: Path,
    size: int = 1024,
) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    colors = [_hex_to_rgb(c) for c in (palette or ["#264653", "#2A9D8F", "#E9C46A"])[:4]]
    while len(colors) < 3:
        colors.append((40, 40, 40))

    bg, accent, secondary = colors[0], colors[1], colors[2]
    style_key = STYLES.get((style or "").lower().strip(), "minimal")
    img = Image.new("RGB", (size, size), bg)
    draw = ImageDraw.Draw(img)
    cx = cy = size // 2
    pad = size // 8

    if style_key == "premium":
        draw.rounded_rectangle([pad, pad, size - pad, size - pad], radius=size // 10, outline=accent, width=size // 40)
        draw.ellipse([cx - size // 5, cy - size // 3, cx + size // 5, cy - size // 12], fill=accent)
    elif style_key == "bold":
        draw.polygon(
            [(cx, pad), (size - pad, cy), (cx, size - pad), (pad, cy)],
            fill=accent,
        )
        draw.ellipse([cx - size // 6, cy - size // 6, cx + size // 6, cy + size // 6], fill=bg)
    elif style_key == "warm":
        for i, col in enumerate([accent, secondary, colors[min(3, len(colors) - 1)]]):
            r = size // 2 - pad - i * size // 12
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=size // 35)
        draw.ellipse([cx - size // 7, cy - size // 7, cx + size // 7, cy + size // 7], fill=accent)
    elif style_key == "tech":
        step = size // 16
        for i in range(pad, size - pad, step):
            alpha = 40 + (i % 3) * 20
            mix = tuple(min(255, int(bg[j] * 0.7 + accent[j] * 0.3)) for j in range(3))
            draw.line([(i, pad), (i, size - pad)], fill=mix, width=2)
        draw.rounded_rectangle(
            [cx - size // 4, cy - size // 4, cx + size // 4, cy + size // 4],
            radius=size // 30,
            fill=accent,
        )
    else:  # minimal
        r = size // 3
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=accent)
        inner = r - size // 12
        draw.ellipse([cx - inner, cy - inner, cx + inner, cy + inner], fill=bg)

    initials = _initials(brand_name)
    font = _font(size // 5)
    bbox = draw.textbbox((0, 0), initials, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    if style_key == "minimal":
        # подложка под инициалы всегда шире текста, иначе буквы вылезают за круг
        disc = int(max(tw, th) * 0.72) + size // 24
        draw.ellipse([cx - disc, cy - disc, cx + disc, cy + disc], fill=secondary)
        text_color = (20, 20, 20) if sum(_hex_to_rgb(palette[2] if len(palette) > 2 else "#EEEEEE")) > 400 else (255, 255, 255)
    else:
        text_color = (255, 255, 255) if sum(accent) < 400 else (20, 20, 20)

    draw.text((cx - tw / 2 - bbox[0], cy - th / 2 - bbox[1]), initials, fill=text_color, font=font)

    # Wordmark strip at bottom
    bar_h = size // 7
    draw.rectangle([0, size - bar_h, size, size], fill=(255, 255, 255))
    name_font = _font(max(28, size // 14))
    label = brand_name[:22]
    bbox = draw.textbbox((0, 0), label, font=name_font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size - tw) / 2, size - bar_h + (bar_h - th) / 2 - 4), label, fill=bg, font=name_font)

    img.save(out_path, "PNG", optimize=True)
    _write_svg(out_path.with_suffix(".svg"), brand_name, palette, initials, style_key)
    return out_path


def _write_svg(path: Path, name: str, palette: list[str], initials: str, style_key: str) -> None:
    bg = palette[0] if palette else "#264653"
    accent = palette[1] if len(palette) > 1 else "#2A9D8F"
    secondary = palette[2] if len(palette) > 2 else "#E9C46A"
    mark = {
        "minimal": f'<circle cx="512" cy="460" r="280" fill="{accent}"/><circle cx="512" cy="460" r="200" fill="{bg}"/><circle cx="512" cy="460" r="90" fill="{secondary}"/>',
        "bold": f'<polygon points="512,120 900,460 512,800 124,460" fill="{accent}"/><circle cx="512" cy="460" r="140" fill="{bg}"/>',
        "premium": f'<rect x="140" y="140" width="744" height="640" rx="80" fill="none" stroke="{accent}" stroke-width="28"/><ellipse cx="512" cy="320" rx="170" ry="120" fill="{accent}"/>',
        "warm": f'<circle cx="512" cy="460" r="300" fill="none" stroke="{accent}" stroke-width="28"/><circle cx="512" cy="460" r="220" fill="none" stroke="{secondary}" stroke-width="22"/><circle cx="512" cy="460" r="120" fill="{accent}"/>',
        "tech": f'<rect x="320" y="280" width="384" height="360" rx="28" fill="{accent}"/>',
    }.get(style_key, "")
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">
  <rect width="1024" height="1024" fill="{bg}"/>
  {mark}
  <text x="512" y="490" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="180" font-weight="700" fill="#ffffff">{initials}</text>
  <rect y="880" width="1024" height="144" fill="#ffffff"/>
  <text x="512" y="970" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="64" font-weight="700" fill="{bg}">{name[:22]}</text>
</svg>
'''
    path.write_text(svg, encoding="utf-8")


def generate_palette_card(brand_name: str, palette: list[str], out_path: Path) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    w, h = 1200, 600
    img = Image.new("RGB", (w, h), (250, 250, 250))
    draw = ImageDraw.Draw(img)
    font = _font(42)
    title_font = _font(56)
    draw.text((48, 36), f"{brand_name} — палитра", fill=(30, 30, 30), font=title_font)
    n = max(1, len(palette))
    box_w = (w - 96 - (n - 1) * 24) // n
    for i, hex_color in enumerate(palette):
        x0 = 48 + i * (box_w + 24)
        y0 = 140
        rgb = _hex_to_rgb(hex_color)
        draw.rounded_rectangle([x0, y0, x0 + box_w, y0 + 320], radius=24, fill=rgb)
        label_color = (255, 255, 255) if sum(rgb) < 400 else (20, 20, 20)
        draw.text((x0 + 20, y0 + 340), hex_color.upper(), fill=(40, 40, 40), font=font)
        draw.text((x0 + 20, y0 + 20), f"C{i+1}", fill=label_color, font=font)
    img.save(out_path, "PNG", optimize=True)
    return out_path
