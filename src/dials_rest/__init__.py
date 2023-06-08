from importlib.metadata import PackageNotFoundError, version

try:
    __version__: str | None = version("dials_rest")
except PackageNotFoundError:
    # package is not installed
    __version__ = None
