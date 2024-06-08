from setuptools import (
    setup,
    find_packages,
)

__version__: str = "0.0.1"

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="tg_notification_bot",
    version=__version__,
    description="Telegram notification bot for python projects",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    url="https://github.com/AI-Stratov/tg_notification_bot",
    include_package_data=True,
    install_requires=[
        "aiogram==2.4",
    ],
)
