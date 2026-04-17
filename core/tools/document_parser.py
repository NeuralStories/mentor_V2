"""
Parsers de documentos para la zona de ingesta.
Soporta PDF, DOCX, TXT y MD con metadata extraida.
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple

from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError
from docx import Document
from docx.opc.exceptions import PackageNotFoundError

from core.config import settings

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

try:
    import pytesseract
except Exception:
    pytesseract = None

try:
    from PIL import Image
except Exception:
    Image = None

logger = logging.getLogger(__name__)


class DocumentParser:
    """
    Parser unificado para multiples formatos de documento.
    Extrae texto y metadata de archivos.
    """

    SUPPORTED_FORMATS = {
        ".pdf": "pdf",
        ".docx": "docx",
        ".txt": "txt",
        ".md": "markdown",
    }

    @staticmethod
    def can_parse(file_path: str) -> bool:
        return Path(file_path).suffix.lower() in DocumentParser.SUPPORTED_FORMATS

    @staticmethod
    def get_format(file_path: str) -> str:
        return DocumentParser.SUPPORTED_FORMATS.get(Path(file_path).suffix.lower(), "unknown")

    @staticmethod
    def parse_file(file_path: str) -> Tuple[str, Dict[str, Any]]:
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

        if not DocumentParser.can_parse(str(file_path)):
            raise ValueError(f"Formato no soportado: {file_path.suffix}")

        format_type = DocumentParser.get_format(str(file_path))
        metadata: Dict[str, Any] = {
            "file_name": file_path.name,
            "file_path": str(file_path),
            "file_size": file_path.stat().st_size,
            "file_format": format_type,
            "upload_date": datetime.now().isoformat(),
            "pages": 1,
            "word_count": 0,
            "char_count": 0,
            "ocr_used": False,
        }

        try:
            if format_type == "pdf":
                content, pdf_metadata = DocumentParser._parse_pdf(file_path)
                metadata.update(pdf_metadata)
            elif format_type == "docx":
                content, docx_metadata = DocumentParser._parse_docx(file_path)
                metadata.update(docx_metadata)
            elif format_type == "txt":
                content = DocumentParser._parse_txt(file_path)
            elif format_type == "markdown":
                content = DocumentParser._parse_markdown(file_path)
            else:
                raise ValueError(f"Parser no implementado para: {format_type}")

            metadata["word_count"] = len(content.split())
            metadata["char_count"] = len(content)
            logger.info(f"Documento parseado: {file_path.name} ({len(content)} caracteres)")
            return content, metadata
        except Exception as e:
            logger.error(f"Error parseando {file_path}: {e}")
            raise

    @staticmethod
    def _parse_pdf(file_path: Path) -> Tuple[str, Dict[str, Any]]:
        try:
            reader = PdfReader(str(file_path))
            pdf_info = reader.metadata
            metadata: Dict[str, Any] = {
                "pages": len(reader.pages),
                "title": pdf_info.title if pdf_info and pdf_info.title else None,
                "author": pdf_info.author if pdf_info and pdf_info.author else None,
                "subject": pdf_info.subject if pdf_info and pdf_info.subject else None,
                "creator": pdf_info.creator if pdf_info and pdf_info.creator else None,
                "ocr_used": False,
            }

            content_parts = []
            for page in reader.pages:
                page_text = page.extract_text() or ""
                if page_text.strip():
                    content_parts.append(page_text.strip())

            content = "\n\n".join(content_parts)
            if not content.strip() and settings.OCR_ENABLED:
                content = DocumentParser._ocr_pdf(file_path)
                metadata["ocr_used"] = bool(content.strip())

            return content.strip(), metadata
        except PdfReadError as e:
            raise ValueError(f"Error leyendo PDF: {e}")

    @staticmethod
    def _parse_docx(file_path: Path) -> Tuple[str, Dict[str, Any]]:
        try:
            doc = Document(str(file_path))
            metadata = {"pages": 1}
            content_parts = []

            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    content_parts.append(paragraph.text.strip())

            for table in doc.tables:
                for row in table.rows:
                    row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_text:
                        content_parts.append(" | ".join(row_text))

            return "\n".join(content_parts).strip(), metadata
        except PackageNotFoundError:
            raise ValueError("Error leyendo DOCX: archivo corrupto o no valido")

    @staticmethod
    def _parse_txt(file_path: Path) -> str:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            for encoding in ["latin-1", "cp1252", "iso-8859-1"]:
                try:
                    with open(file_path, "r", encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            raise ValueError("No se pudo decodificar el archivo de texto")

    @staticmethod
    def _parse_markdown(file_path: Path) -> str:
        return DocumentParser._parse_txt(file_path)

    @staticmethod
    def _ocr_pdf(file_path: Path) -> str:
        if not settings.OCR_ENABLED:
            return ""
        if fitz is None or pytesseract is None or Image is None:
            logger.warning("OCR habilitado pero faltan dependencias opcionales")
            return ""

        if settings.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

        try:
            doc = fitz.open(str(file_path))
            text_parts = []
            for page in doc:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                page_text = pytesseract.image_to_string(image, lang=settings.OCR_LANGUAGE)
                if page_text.strip():
                    text_parts.append(page_text.strip())
            return "\n\n".join(text_parts)
        except Exception as e:
            logger.warning(f"OCR no disponible para {file_path.name}: {e}")
            return ""

    @staticmethod
    def validate_file(file_path: str, max_size_mb: int = 50) -> Tuple[bool, str]:
        try:
            path = Path(file_path)
            if not path.exists():
                return False, "Archivo no encontrado"

            size_mb = path.stat().st_size / (1024 * 1024)
            if size_mb > max_size_mb:
                return False, f"Archivo demasiado grande ({size_mb:.1f}MB > {max_size_mb}MB)"

            if not DocumentParser.can_parse(file_path):
                return False, f"Formato no soportado: {path.suffix}"

            if path.stat().st_size == 0:
                return False, "Archivo vacio"

            return True, "Archivo valido"
        except Exception as e:
            return False, f"Error validando archivo: {e}"
