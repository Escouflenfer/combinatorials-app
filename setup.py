from setuptools import setup, find_packages

setup(
    name="Combinatorials data app",              # Name of the project
    version="0.1.0",                  # Version
    packages=find_packages(),         # Automatically find all packages in your_project/
    install_requires=[],
    entry_points={
        "console_scripts": [
            # Add CLI commands if you have any
        ],
    },
)
