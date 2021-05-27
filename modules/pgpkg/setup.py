from setuptools import setup


setup(
    name="pgpkg",
    version="0.1.0",
    packages=["pgpkg"],
    url="https://github.com/brendan-ward/pgpkg",
    license="MIT",
    author="Brendan C. Ward",
    author_email="bcward@astutespruce.com",
    description="Faster I/O between pygeos and geopackages",
    long_description_content_type="text/markdown",
    long_description=open("README.md").read(),
    install_requires=["pygeos", "pandas", "numpy", "pyproj"],
    tests_require=["geopandas", "pytest", "pytest-cov", "pytest-benchmark"],
    include_package_data=True,
)
