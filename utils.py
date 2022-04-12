import config


def red(string):
    """Return the given string, bookended with control codes for printing in red."""
    if not config.OUTPUT_TO_FILE:
        return f"\033[91m{string}\x1b[0m"
    return string


def green(string):
    """Return the given string, bookended with control codes for printing in green."""
    if not config.OUTPUT_TO_FILE:
        return f"\033[92m{string}\x1b[0m"
    return string


def blue(string):
    """Return the given string, bookended with control codes for printing in blue."""
    if not config.OUTPUT_TO_FILE:
        return f"\033[94m{string}\x1b[0m"
    return string


def yellow(string):
    """Return the given string, bookended with control codes for printing in yellow."""
    if not config.OUTPUT_TO_FILE:
        return f"\033[93m{string}\x1b[0m"
    return string
