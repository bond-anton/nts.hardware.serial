"""Mock functions collection."""


def mock_openpty():
    """Mock os.openpty to raise an OSError."""
    raise OSError("Failed to create pseudo-terminal")
