def verify_token_format(token):
    """
    Verify the format of the token.

    Args:
        token (str): The token to be verified.

    Raises:
        AssertionError: If the token does not meet the required format criteria.
    """
    assert token is not None, "Token should not be None"
    assert token != "", "Token should not be an empty string"
    assert isinstance(token, str), "Token should be a string"
    assert " " not in token, "Token should not contain any whitespace"
    assert any(c.isupper() for c in token), "The string must contain uppercase letters."
    assert any(c.islower() for c in token), "The string must contain lowercase letters."
    assert any(c.isdigit() for c in token), "The string must contain digits."
