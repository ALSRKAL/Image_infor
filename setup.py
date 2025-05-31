from setuptools import setup, find_packages
from pathlib import Path
import sys

# Read the contents of README.md
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Version
__version__ = "2.0.0"

# Dependencies
install_requires = [
    'Pillow>=10.0.0',
    'PyQt5>=5.15.0',
    'requests>=2.31.0',
    'python-dotenv>=1.0.0',
]

# Platform-specific dependencies
platform_specific = {
    'win32': ['pywin32>=300'],
    'darwin': ['pyobjc>=9.0.0'],
}

# Development dependencies
extras_require = {
    'dev': [
        'pytest>=7.0.0',
        'coverage>=6.0.0',
        'black>=22.0.0',
        'isort>=5.0.0',
        'flake8>=4.0.0',
        'mypy>=0.900',
    ],
    'docs': [
        'sphinx>=4.0.0',
        'sphinx-rtd-theme>=1.0.0',
        'sphinx-autodoc-typehints>=1.18.0',
    ]
}

# Add platform-specific dependencies
for platform, deps in platform_specific.items():
    if sys.platform.startswith(platform):
        install_requires.extend(deps)

setup(
    name="image-metadata-viewer",
    version=__version__,
    author="Your Name",
    author_email="your.email@example.com",
    description="A cross-platform tool for viewing and managing image metadata",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/alsrkal/Image_info",
    project_urls={
        "Bug Tracker": "https://github.com/alsrkal/Image_info/issues",
        "Source": "https://github.com/alsrkal/Image_info"
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Utilities",
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.8",
    install_requires=install_requires,
    extras_require=extras_require,
    entry_points={
        'console_scripts': [
            'image-metadata-viewer=image_metadata_viewer.__main__:main',
        ],
        'gui_scripts': [
            'image-metadata-viewer-gui=image_metadata_viewer.__main__:main',
        ]
    },
    package_data={
        'image_metadata_viewer': ['*.ui', 'resources/*'],
    },
    include_package_data=True,
    zip_safe=False,
    keywords=[
        'image', 'metadata', 'viewer', 'exif', 'gps', 'location', 'photo'
    ],
    project_urls={
        'Documentation': 'https://image-metadata-viewer.readthedocs.io',
        'Source': 'https://github.com/alsrkal/image-metadata-viewer',
        'Tracker': 'https://github.com/alsrkal/image-metadata-viewer/issues'
    }
)
