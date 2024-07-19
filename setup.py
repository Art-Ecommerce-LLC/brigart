from setuptools import setup, find_packages

setup(
    name='BrigArtAPI',
    version='0.1',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'itsdangerous==2.1.2',
        'requests==2.31.0',
        'fastapi==0.110.0',
        'Jinja2==3.1.3',
        'pydantic==2.6.3',
        'python-dotenv==1.0.1',
        'urllib3==2.2.1',
        'uvicorn==0.27.1',
        'starlette==0.36.3',
        'email_validator==2.1.1',
        'smartystreets_python_sdk==4.14.2',
        'python-multipart==0.0.9',
        'pillow==8.3.2',
        'aiohttp==3.9.5',
        'loguru==0.7.2',
        'slowapi==0.1.9',
        'websockets==12.0'
    ],
    entry_points={
        'console_scripts': [
            'brigartapi=app:main',
        ],
    },
)