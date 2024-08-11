from setuptools import setup, find_packages

setup(
    name='BrigArtAPI',
    version='0.1',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'itsdangerous==2.2.0',
        'requests==2.32.3',
        'fastapi==0.112.0',
        'Jinja2==3.1.4',
        'pydantic==2.8.2',
        'python-dotenv==1.0.1',
        'urllib3==2.2.2',
        'uvicorn==0.30.5',
        'starlette==0.36.3',
        'python-multipart==0.0.9',
        'pillow==10.4.0',
        'aiohttp==3.10.3',
        'pillow == 8.3.2',
        'loguru == 0.7.2',
        'stripe == 10.7.0',
        'slowapi==0.1.9',
    ],
    entry_points={
        'console_scripts': [
            'brigartapi=app:main',
        ],
    },
)