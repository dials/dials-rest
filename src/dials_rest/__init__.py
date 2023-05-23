from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("dials_rest")
except PackageNotFoundError:
    # package is not installed
    __version__ = None
