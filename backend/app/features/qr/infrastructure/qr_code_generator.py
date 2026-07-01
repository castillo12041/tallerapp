from __future__ import annotations

import base64
from io import BytesIO


class QrCodeGenerator:
    """
    Genera imágenes QR en formato PNG (base64).
    Utiliza la biblioteca `qrcode[pil]` con lazy import para no romper
    entornos sin Pillow instalado (los tests mockean esta clase).
    """

    def generate_b64(self, content: str, box_size: int = 10, border: int = 4) -> str:
        """Genera un QR PNG y lo retorna como string base64."""
        try:
            import qrcode  # lazy import
            from qrcode.constants import ERROR_CORRECT_M
        except ImportError as exc:
            raise RuntimeError(
                "qrcode no está instalado. Ejecutar: pip install 'qrcode[pil]'"
            ) from exc

        qr = qrcode.QRCode(
            version=None,
            error_correction=ERROR_CORRECT_M,
            box_size=box_size,
            border=border,
        )
        qr.add_data(content)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()
