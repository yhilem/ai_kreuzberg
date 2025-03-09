from __future__ import annotations

from typing import Final

_SUPPORTED_EASYOCR: Final[set[str]] = {
    "abq",
    "ady",
    "af",
    "ang",
    "ar",
    "as",
    "ava",
    "az",
    "be",
    "bg",
    "bh",
    "bho",
    "bn",
    "bs",
    "ch_sim",
    "ch_tra",
    "che",
    "cs",
    "cy",
    "da",
    "dar",
    "de",
    "en",
    "es",
    "et",
    "fa",
    "fr",
    "ga",
    "gom",
    "hi",
    "hr",
    "hu",
    "id",
    "inh",
    "is",
    "it",
    "ja",
    "kbd",
    "kn",
    "ko",
    "ku",
    "la",
    "lbe",
    "lez",
    "lt",
    "lv",
    "mah",
    "mai",
    "mi",
    "mn",
    "mr",
    "ms",
    "mt",
    "ne",
    "new",
    "nl",
    "no",
    "oc",
    "pi",
    "pl",
    "pt",
    "ro",
    "ru",
    "rs_cyrillic",
    "rs_latin",
    "sck",
    "sk",
    "sl",
    "sq",
    "sv",
    "sw",
    "ta",
    "tab",
    "te",
    "th",
    "tjk",
    "tl",
    "tr",
    "ug",
    "uk",
    "ur",
    "uz",
    "vi",
}

_SUPPORTED_PADDLE: Final[set[str]] = {"ch", "en", "french", "german", "japan", "korean"}

_SUPPORTED_TESSERACT: Final[set[str]] = {
    "afr",
    "amh",
    "ara",
    "asm",
    "aze",
    "aze_cyrl",
    "bel",
    "ben",
    "bod",
    "bos",
    "bre",
    "bul",
    "cat",
    "ceb",
    "ces",
    "chi_sim",
    "chi_tra",
    "chr",
    "cos",
    "cym",
    "dan",
    "dan_frak",
    "deu",
    "deu_frak",
    "deu_latf",
    "dzo",
    "ell",
    "eng",
    "enm",
    "epo",
    "equ",
    "est",
    "eus",
    "fao",
    "fas",
    "fil",
    "fin",
    "fra",
    "frk",
    "frm",
    "fry",
    "gla",
    "gle",
    "glg",
    "grc",
    "guj",
    "hat",
    "heb",
    "hin",
    "hrv",
    "hun",
    "hye",
    "iku",
    "ind",
    "isl",
    "ita",
    "ita_old",
    "jav",
    "jpn",
    "kan",
    "kat",
    "kat_old",
    "kaz",
    "khm",
    "kir",
    "kmr",
    "kor",
    "kor_vert",
    "kur",
    "lao",
    "lat",
    "lav",
    "lit",
    "ltz",
    "mal",
    "mar",
    "mkd",
    "mlt",
    "mon",
    "mri",
    "msa",
    "mya",
    "nep",
    "nld",
    "nor",
    "oci",
    "ori",
    "osd",
    "pan",
    "pol",
    "por",
    "pus",
    "que",
    "ron",
    "rus",
    "san",
    "sin",
    "slk",
    "slk_frak",
    "slv",
    "snd",
    "spa",
    "spa_old",
    "sqi",
    "srp",
    "srp_latn",
    "sun",
    "swa",
    "swe",
    "syr",
    "tam",
    "tat",
    "tel",
    "tgk",
    "tgl",
    "tha",
    "tir",
    "ton",
    "tur",
    "uig",
    "ukr",
    "urd",
    "uzb",
    "uzb_cyrl",
    "vie",
    "yid",
    "yor",
}


_ISO_TO_EASYOCR: Final[dict[str, str]] = {
    "abk": "abq",
    "ady": "ady",
    "af": "af",
    "afr": "af",
    "ang": "ang",
    "ar": "ar",
    "ara": "ar",
    "asm": "as",
    "ava": "ava",
    "az": "az",
    "aze": "az",
    "be": "be",
    "bel": "be",
    "ben": "bn",
    "bg": "bg",
    "bho": "bho",
    "bih": "bh",
    "bn": "bn",
    "bos": "bs",
    "bs": "bs",
    "bul": "bg",
    "cat": "ca",
    "ces": "cs",
    "che": "che",
    "cs": "cs",
    "cy": "cy",
    "cym": "cy",
    "da": "da",
    "dan": "da",
    "dar": "dar",
    "de": "de",
    "deu": "de",
    "el": "el",
    "en": "en",
    "eng": "en",
    "es": "es",
    "est": "et",
    "et": "et",
    "fa": "fa",
    "fas": "fa",
    "fil": "tl",
    "fin": "fi",
    "fr": "fr",
    "fra": "fr",
    "ga": "ga",
    "gle": "ga",
    "guj": "gu",
    "he": "he",
    "heb": "he",
    "hi": "hi",
    "hin": "hi",
    "hr": "hr",
    "hrv": "hr",
    "hu": "hu",
    "hun": "hu",
    "id": "id",
    "ind": "id",
    "inh": "inh",
    "is": "is",
    "isl": "is",
    "it": "it",
    "ita": "it",
    "ja": "ja",
    "jpn": "ja",
    "kan": "kn",
    "kbd": "kbd",
    "kn": "kn",
    "ko": "ko",
    "kor": "ko",
    "ku": "ku",
    "kur": "ku",
    "la": "la",
    "lat": "la",
    "lav": "lv",
    "lbe": "lbe",
    "lez": "lez",
    "lit": "lt",
    "lt": "lt",
    "lv": "lv",
    "mah": "mah",
    "mai": "mai",
    "mal": "ml",
    "mar": "mr",
    "mi": "mi",
    "mkd": "mk",
    "ml": "ml",
    "mlt": "mt",
    "mn": "mn",
    "mon": "mn",
    "mr": "mr",
    "mri": "mi",
    "ms": "ms",
    "msa": "ms",
    "mt": "mt",
    "ne": "ne",
    "nep": "ne",
    "new": "new",
    "nl": "nl",
    "nld": "nl",
    "no": "no",
    "nor": "no",
    "oc": "oc",
    "oci": "oc",
    "or": "or",
    "ori": "or",
    "pa": "pa",
    "pan": "pa",
    "pi": "pi",
    "pli": "pi",
    "pl": "pl",
    "pol": "pl",
    "por": "pt",
    "pt": "pt",
    "ro": "ro",
    "ron": "ro",
    "rs_cyrillic": "rs_cyrillic",
    "rs_latin": "rs_latin",
    "ru": "ru",
    "rus": "ru",
    "sa": "sa",
    "san": "sa",
    "sck": "sck",
    "sd": "sd",
    "si": "si",
    "sin": "si",
    "sk": "sk",
    "slk": "sk",
    "sl": "sl",
    "slv": "sl",
    "snd": "sd",
    "spa": "es",
    "sq": "sq",
    "sqi": "sq",
    "sr": "sr",
    "sr_cyrl": "rs_cyrillic",
    "sr_latn": "rs_latin",
    "srp": "sr",
    "srp_cyrl": "rs_cyrillic",
    "srp_latn": "rs_latin",
    "sv": "sv",
    "swa": "sw",
    "swe": "sv",
    "sw": "sw",
    "tab": "tab",
    "ta": "ta",
    "tam": "ta",
    "tat": "tt",
    "te": "te",
    "tel": "te",
    "tgk": "tjk",
    "th": "th",
    "tha": "th",
    "tjk": "tjk",
    "tl": "tl",
    "tgl": "tl",
    "tr": "tr",
    "tur": "tr",
    "tt": "tt",
    "ug": "ug",
    "uig": "ug",
    "uk": "uk",
    "ukr": "uk",
    "ur": "ur",
    "urd": "ur",
    "uz": "uz",
    "uzb": "uz",
    "vi": "vi",
    "vie": "vi",
    "zh": "ch_sim",
    "zh_hans": "ch_sim",
    "zh_hant": "ch_tra",
    "zho": "ch_sim",
    "zho_hans": "ch_sim",
    "zho_hant": "ch_tra",
}

_ISO_TO_PADDLE: Final[dict[str, str]] = {
    "de": "german",
    "deu": "german",
    "en": "en",
    "eng": "en",
    "fr": "french",
    "fra": "french",
    "ja": "japan",
    "jpn": "japan",
    "ko": "korean",
    "kor": "korean",
    "zh": "ch",
    "zh_hans": "ch",
    "zh_hant": "ch",
    "zho": "ch",
    "zho_hans": "ch",
    "zho_hant": "ch",
}

_ISO_TO_TESSERACT: Final[dict[str, str]] = {
    "cs": "ces",
    "de": "deu",
    "el": "ell",
    "fa": "fas",
    "fr": "fra",
    "he": "heb",
    "hr": "hrv",
    "hy": "hye",
    "is": "isl",
    "ja": "jpn",
    "ka": "kat",
    "ko": "kor",
    "nb": "nor",
    "nn": "nor",
    "ro": "ron",
    "sk": "slk",
    "sq": "sqi",
    "sr": "srp",
    "uk": "ukr",
    "vi": "vie",
    "yi": "yid",
    "yo": "yor",
    "zh": "chi_sim",
    "zh_hans": "chi_sim",
    "zh_hant": "chi_tra",
    "zho": "chi_sim",
    "zho_hans": "chi_sim",
    "zho_hant": "chi_tra",
}


def to_easyocr(lang_code: str) -> list[str]:
    """Convert language code(s) to EasyOCR format.

    Args:
        lang_code: ISO language code(s) or language name(s)

    Returns:
        List of language codes compatible with EasyOCR
    """
    normalized = lang_code.lower()
    easyocr_lang = _ISO_TO_EASYOCR.get(normalized, normalized)

    if easyocr_lang in _SUPPORTED_EASYOCR:
        return [easyocr_lang]

    return ["en"]


def to_paddle(lang_code: str) -> str:
    """Convert a language code to PaddleOCR format.

    Args:
        lang_code: ISO language code or language name

    Returns:
        Language code compatible with PaddleOCR, defaults to "en" if not supported
    """
    normalized = lang_code.lower()
    paddle_lang = _ISO_TO_PADDLE.get(normalized, normalized)

    if paddle_lang in _SUPPORTED_PADDLE:
        return paddle_lang

    return "en"


def to_tesseract(lang_code: str) -> str:
    """Convert a language code to Tesseract format.

    Args:
        lang_code: ISO language code or language name

    Returns:
        Language code compatible with Tesseract, defaults to "eng" if not supported
    """
    normalized = lang_code.lower()
    tesseract_lang = _ISO_TO_TESSERACT.get(normalized, normalized)

    if tesseract_lang in _SUPPORTED_TESSERACT:
        return tesseract_lang

    return "eng"


def is_supported_by_easyocr(lang_code: str) -> bool:
    """Check if a language is supported by EasyOCR.

    Args:
        lang_code: ISO language code or language name

    Returns:
        True if the language is supported by EasyOCR
    """
    normalized = lang_code.lower()
    easyocr_lang = _ISO_TO_EASYOCR.get(normalized, normalized)
    return easyocr_lang in _SUPPORTED_EASYOCR


def is_supported_by_paddle(lang_code: str) -> bool:
    """Check if a language is supported by PaddleOCR.

    Args:
        lang_code: ISO language code or language name

    Returns:
        True if the language is supported by PaddleOCR
    """
    normalized = lang_code.lower()
    paddle_lang = _ISO_TO_PADDLE.get(normalized, normalized)
    return paddle_lang in _SUPPORTED_PADDLE


def is_supported_by_tesseract(lang_code: str) -> bool:
    """Check if a language is supported by Tesseract.

    Args:
        lang_code: ISO language code or language name

    Returns:
        True if the language is supported by Tesseract
    """
    normalized = lang_code.lower()
    tesseract_lang = _ISO_TO_TESSERACT.get(normalized, normalized)
    return tesseract_lang in _SUPPORTED_TESSERACT
