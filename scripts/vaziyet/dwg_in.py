"""DWG girdisi (DEV-087): DIS ARAC SARMALI. `ezdxf` DWG okumaz; bu modul kurulu bir donusturucuyu (LibreDWG `dwg2dxf` ya da ODA File Converter) cagirir,
cikan DXF'i AYNI aday/onay hattindan (`scan_site_dxf`) gecirir. Arac kurulu degilse ya da basarisizsa ACIK hata verilir (sessiz yutma yok, "DXF olarak kaydedin" denir).

Arac secimi bir LISANS/KURULUM kararidir ve kullanicidadir; kod hicbir araci paketlemez. Arama sirasi: ortam degiskeni `VAZIYET_DWG_CONVERTER` (tam yol),
PATH'te `dwg2dxf`, PATH'te `ODAFileConverter`."""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

try:
    from .dxf_in import DxfInputError, SiteScan, scan_site_dxf
except ImportError:
    from dxf_in import DxfInputError, SiteScan, scan_site_dxf  # type: ignore

ENV_VAR = "VAZIYET_DWG_CONVERTER"
CONVERT_TIMEOUT_S = 300          # donusturucu takilirsa durdurma suresi (calisma korkulugu; tasarim esigi degil)
ODA_OUTPUT_VERSION = "ACAD2018"   # ODA File Converter cikti surumu (ezdxf bu surumu okur)
INSTALL_HINT = "DWG donusturucu bulunamadi. Secenekler: (a) CAD'de 'DXF olarak kaydedin' (kod gerekmez); (b) LibreDWG `dwg2dxf` ya da ODA File Converter kurup PATH'e ekleyin " \
               f"(ya da {ENV_VAR}=<tam yol> verin)."


@dataclass(frozen=True)
class ConversionRecord:
    tool: str                 # 'dwg2dxf' | 'ODAFileConverter'
    tool_path: str
    dwg_sha256: str
    dxf_sha256: str


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def find_converter(env: dict | None = None) -> tuple[str, str] | None:
    """(tur, tam yol) | None. Tur, dosya adindan: 'ODAFileConverter' iceren -> ODA; digerleri LibreDWG tarzi (`dwg2dxf -y -o cikti.dxf girdi.dwg`)."""
    env = os.environ if env is None else env
    explicit = env.get(ENV_VAR)
    if explicit:
        if not Path(explicit).exists():
            raise DxfInputError(f"{ENV_VAR} gosterilen donusturucu yok: {explicit}")
        return ("ODAFileConverter" if "odafileconverter" in Path(explicit).name.lower() else "dwg2dxf"), explicit
    for name, kind in (("dwg2dxf", "dwg2dxf"), ("ODAFileConverter", "ODAFileConverter")):
        found = shutil.which(name, path=env.get("PATH"))
        if found:
            return kind, found
    return None


def convert_dwg(dwg_path, out_dir, converter: tuple[str, str] | None = None) -> tuple[Path, ConversionRecord]:
    """DWG -> DXF (`out_dir` icinde). Donusturucu yoksa/basarisizsa `DxfInputError` (aciklama + kurulum ipucu)."""
    src = Path(dwg_path)
    if not src.exists():
        raise DxfInputError(f"dosya yok: {src}")
    if not src.read_bytes()[:4].startswith(b"AC10"):
        raise DxfInputError(f"{src.name} bir DWG dosyasi degil (AC10xx basligi yok)")
    conv = converter or find_converter()
    if conv is None:
        raise DxfInputError(INSTALL_HINT)
    kind, exe = conv
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / (src.stem + ".dxf")
    if kind == "ODAFileConverter":
        cmd = [exe, str(src.parent), str(out_dir), ODA_OUTPUT_VERSION, "DXF", "0", "1", src.name]
    else:
        cmd = [exe, "-y", "-o", str(out), str(src)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=CONVERT_TIMEOUT_S)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DxfInputError(f"DWG donusturucu calistirilamadi/zaman asimi ({kind}): {exc}. CAD'de 'DXF olarak kaydedin'.") from exc
    if r.returncode != 0:
        raise DxfInputError(f"DWG donusturucu hata verdi ({kind}, cikis {r.returncode}): {(r.stderr or r.stdout).strip()[:300]}. CAD'de 'DXF olarak kaydedin'.")
    if not out.exists() or out.stat().st_size == 0:
        raise DxfInputError(f"DWG donusturucu ({kind}) cikti DXF'i uretmedi: {out}. CAD'de 'DXF olarak kaydedin'.")
    return out, ConversionRecord(kind, exe, _sha(src), _sha(out))


def scan_site_dwg(dwg_path, converter: tuple[str, str] | None = None, work_dir=None) -> tuple[SiteScan, ConversionRecord]:
    """DWG -> DXF -> `scan_site_dxf`. Dondurulen `SiteScan.path/sha256` KAYNAK DWG'yi gosterir (kayit: donusturulen DXF degil, kullanicinin dosyasi);
    donusum kaydi (arac + DXF sha256) ayrica doner. Aday secimi/onay hatti DXF ile AYNIDIR."""
    if work_dir is not None:
        out, rec = convert_dwg(dwg_path, work_dir, converter)
        scan = scan_site_dxf(out)
    else:
        with tempfile.TemporaryDirectory() as tmp:
            out, rec = convert_dwg(dwg_path, tmp, converter)
            scan = scan_site_dxf(out)
    scan.path = str(dwg_path)
    scan.sha256 = rec.dwg_sha256
    return scan, rec
