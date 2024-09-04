def pascal_to_kebab(s: str) -> str:
    """Convert a string of the form 'SomeThing' to 'some-thing'."""
    # Split the string into words.
    words = []
    word = ""
    for c in s:
        if c.isupper():
            # Start a new word.
            if word:
                words.append(word)
            word = c.lower()
        else:
            word += c
    if word:
        words.append(word)
    # Join the words with hyphens.
    return "-".join(words)


def kebab_to_pascal(s: str) -> str:
    """Convert a string of the form 'some-thing' to 'SomeThing'."""
    # Split the string into words.
    words = s.split("-")
    # Capitalize the first letter of each word.
    return "".join(word.capitalize() for word in words)
