from setuptools import find_packages, setup

setup(
    name="suno_songs",
    version="0.2.0",
    author="yihong0618",
    author_email="zouzou0208@gmail.com",
    description="High quality image generation by ideogram.ai. Reverse engineered API.",
    url="https://github.com/yihong0618/SunoSongsCreator",
    project_urls={
        "Bug Report": "https://github.com/yihong0618/SunoSongsCreator/issues/new",
    },
    install_requires=[
        "curl_cffi",
        "requests",
        "fake-useragent",
        "rich",
    ],
    packages=find_packages(),
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    entry_points={
        "console_scripts": ["suno = suno.suno:main"],
    },
    classifiers=[
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
