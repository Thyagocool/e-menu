def normalize_phone(value: str | None) -> str:
    """Dígitos apenas, com DDI 55 quando ausente (número brasileiro)."""
    if not value:
        return ""
    digits = "".join(ch for ch in value if ch.isdigit())
    if len(digits) <= 11:
        digits = f"55{digits}"
    return digits