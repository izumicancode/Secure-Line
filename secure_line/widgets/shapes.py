"""Low-level canvas drawing primitives (rounded rectangles) other widget
factories build on."""


def _round_rect_points(x1, y1, x2, y2, radii):
    """radii = (top_left, top_right, bottom_right, bottom_left)"""
    tl, tr, br, bl = radii
    return [
        x1 + tl, y1, x2 - tr, y1, x2, y1, x2, y1 + tr,
        x2, y2 - br, x2, y2, x2 - br, y2, x1 + bl, y2,
        x1, y2, x1, y2 - bl, x1, y1 + tl, x1, y1,
    ]


def draw_round_rect(canvas, x1, y1, x2, y2, radii, **kwargs):
    pts = _round_rect_points(x1, y1, x2, y2, radii)
    return canvas.create_polygon(pts, smooth=True, splinesteps=24, **kwargs)


def _lerp_color(c1: str, c2: str, t: float) -> str:
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = round(r1 + (r2 - r1) * t)
    g = round(g1 + (g2 - g1) * t)
    b = round(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def human_file_size(n: int) -> str:
    size = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{n} B"
