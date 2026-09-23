"""Proje geneli yazi tipi ve DXF text style yonetimi.

Bu modul, cizimde kullanilan YAZI TIPLERININ tek sahibidir (bkz.
scripts/typography/CLAUDE.md). Iki is yapar:

1. `ensure(doc)` DXF text style'larini kaydeder. Proje geneli font,
   **`Standard` text style'inin fontu degistirilerek** uygulanir - boylece
   acikca stil verilmeyen HER metin (pafta anteti, aks baloncugu, cephe kat
   etiketi, kapak blogu ve DIMSTYLE uzerinden olcu metni dahil) otomatik
   olarak proje fontunu kullanir. Tek tek her `add_text` cagrisina stil
   gecirmek gerekmez.
2. `font_of(role)` ile metin sigdirma hesaplarinin (`pafta.fit_text_height`)
   GERCEKTE cizilecek fontla olcum yapmasini saglar. Bu ikisi ayrisirsa
   metinler pafta disina tasar - bu proje gecmisinde gercekten yasanmis bir
   hata sinifidir.

ROL kavrami: Farkli cizim ogeleri farkli font isteyebilir. Bugun iki rol var:
`default` (proje geneli) ve `room_label` (mahal etiketi). Roller
`meta.fonts` ile context.json'dan override edilebilir; verilmezse ikisi de
Arial Narrow olur.

**DIKKAT - font adi degil DOSYA adi:** ezdxf'e "arialn.ttf" verilmelidir.
"ArialNarrow" gibi bir aile adi sessizce Arial'e duser ve olcum yanlis cikar
(dogrulandi: 'SALON' icin arialn.ttf 388.3, arial.ttf 473.6 birim).
"""
from __future__ import annotations

# Proje varsayilan fontu: Arial Narrow. DOSYA adi olmali (yukaridaki uyari).
DEFAULT_FONT_FILE = "arialn.ttf"

# ezdxf'in her belgede hazir olusturdugu text style. Proje geneli fontu
# bunun uzerine yazarak uygularız; boylece stil verilmeyen tum metinler
# otomatik olarak proje fontunu kullanir.
STANDARD_STYLE = "Standard"

ROLE_DEFAULT = "default"
ROLE_ROOM_LABEL = "room_label"
ROLES = (ROLE_DEFAULT, ROLE_ROOM_LABEL)

_MAX_STYLE_NAME = 31  # DXF sembol adi sinirini asma


def style_name_for(font_file: str) -> str:
    """Font dosya adindan gecerli bir DXF text style adi turetir."""
    stem = font_file.rsplit(".", 1)[0]
    cleaned = "".join(ch for ch in stem.upper() if ch.isalnum() or ch in "_-")
    return cleaned[:_MAX_STYLE_NAME] or "TEXT"


class TextStyles:
    """Rol -> font eslesmesini tutar ve DXF text style'larini kaydeder."""

    def __init__(self, fonts: dict[str, str] | None = None):
        declared = dict(fonts or {})
        default_font = declared.get(ROLE_DEFAULT) or DEFAULT_FONT_FILE
        self.fonts: dict[str, str] = {ROLE_DEFAULT: default_font}
        for role in ROLES:
            if role == ROLE_DEFAULT:
                continue
            self.fonts[role] = declared.get(role) or default_font

    @classmethod
    def from_context(cls, meta: dict) -> "TextStyles":
        """`meta.fonts` verilmisse onu kullanir; verilmemisse Arial Narrow."""
        return cls(meta.get("fonts") or {})

    def font_of(self, role: str = ROLE_DEFAULT) -> str:
        return self.fonts.get(role, self.fonts[ROLE_DEFAULT])

    def style_of(self, role: str = ROLE_DEFAULT) -> str:
        """Rolun DXF text style adi. Proje geneli fontla ayni ise `Standard`
        dondurur - o rol icin ayri bir stil kaydetmeye gerek yoktur."""
        if self.font_of(role) == self.fonts[ROLE_DEFAULT]:
            return STANDARD_STYLE
        return style_name_for(self.font_of(role))

    def ensure(self, doc) -> None:
        """Proje fontunu `Standard`a yazar ve farkli font isteyen roller icin
        ayri text style kaydeder. `ezdxf.new(...)` sonrasinda, herhangi bir
        metin cizilmeden ONCE cagrilmalidir."""
        doc.styles.get(STANDARD_STYLE).dxf.font = self.fonts[ROLE_DEFAULT]
        for role in ROLES:
            name = self.style_of(role)
            if name == STANDARD_STYLE or name in doc.styles:
                continue
            doc.styles.add(name, font=self.font_of(role))


# Bu modulun CONTEXT SOZLESMESI surumu (DEV-020). KOD surumu DEGILDIR:
# yalnizca bu modulun context.json'dan OKUDUGU alanlar degistiginde artar;
# refactor artirmaz. Bkz. scripts/version.py
CONTRACT_VERSION = "1.0"

__all__ = [
    "DEFAULT_FONT_FILE",
    "ROLES",
    "ROLE_DEFAULT",
    "ROLE_ROOM_LABEL",
    "STANDARD_STYLE",
    "TextStyles",
    "style_name_for",
]
