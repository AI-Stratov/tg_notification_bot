from setuptools import setup, find_packages

setup(
    name='tg_notification_bot',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'fastapi',
        'uvicorn',
        'python-telegram-bot'
    ],
    description='A library to integrate Telegram bot with FastAPI',
    author='Your Name',
    author_email='your.email@example.com',
    url='https://github.com/yourusername/my_telegram_library',
)
