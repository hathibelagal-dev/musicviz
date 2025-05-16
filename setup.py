from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="musicviz",
    version="0.0.4",
    author="Ashraff Hathibelagal",
    description="A really simple music visualization tool.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hathibelagal-dev/musicviz",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=[
        "moviepy==1.0.3",
        "librosa==0.10.2.post1",
        "matplotlib==3.10.3",
        "numpy==2.0.2"        
    ],
    entry_points={
        "console_scripts": [
            "musicviz=musicviz.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="ai text-to-speech speech-synthesis nlp transformer voice",
    project_urls={
        "Source": "https://github.com/hathibelagal-dev/musicviz",
        "Tracker": "https://github.com/hathibelagal-dev/musicviz/issues",
    }
)
