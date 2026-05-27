def tex_escape(text: str) -> str:
    """
    A critical safety net that completely neutralizes any LaTeX-breaking characters found within file paths or code structures, preventing compilation crashes.

    Args: text (str): The unsafe string.

    Returns: str: The utterly neutralized string.
    """
    replacements = [
        ("\\", r"\textbackslash{}"),
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
        (">", r"\textgreater{}"),
        ("<", r"\textless{}"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text
