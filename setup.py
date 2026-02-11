from setuptools import setup, find_packages

setup(
    name="concert-split",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "yt-dlp>=2024.1.0",
        "faster-whisper>=1.0.0",
        "mutagen>=1.47.0",
        "click>=8.1.0",
    ],
    entry_points={
        "console_scripts": [
            "concert-split=concert_split.cli:cli",
        ],
    },
)
