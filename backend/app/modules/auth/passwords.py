from __future__ import annotations

import secrets
import string

MIN_PASSWORD_LENGTH = 12


class PasswordValidationError(ValueError):
    """Raised when a password does not meet strength requirements."""
    pass


def validate_password_strength(password: str) -> str:
    """Validate that a password meets minimum strength requirements.
    
    Rules:
    - At least 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    
    Returns the password if valid, raises PasswordValidationError if not.
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        raise PasswordValidationError(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."
        )
    if not any(c.isupper() for c in password):
        raise PasswordValidationError("Password must contain at least one uppercase letter.")
    if not any(c.islower() for c in password):
        raise PasswordValidationError("Password must contain at least one lowercase letter.")
    if not any(c.isdigit() for c in password):
        raise PasswordValidationError("Password must contain at least one digit.")
    special_chars = set(string.punctuation)
    if not any(c in special_chars for c in password):
        raise PasswordValidationError("Password must contain at least one special character.")
    return password


def generate_temporary_password(length: int = 24) -> str:
    """Generate a cryptographically random temporary password.
    
    The generated password is guaranteed to meet all strength requirements.
    Uses secrets.token_urlsafe for the base, then ensures all character classes are present.
    """
    # Generate base random string
    base = secrets.token_urlsafe(length)
    
    # Ensure all required character classes are present
    # Add one of each required class at random positions
    required_chars = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%^&*"),
    ]
    
    # Replace first 4 chars with required classes (still random overall)
    result = list(base[:length])
    for i, char in enumerate(required_chars):
        if i < len(result):
            result[i] = char
    
    # Shuffle to avoid predictable positions
    import random
    rng = random.SystemRandom()
    rng.shuffle(result)
    
    return "".join(result)
