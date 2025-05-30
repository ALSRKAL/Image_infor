from setuptools import setup, find_packages

setup(
    name="image-metadata-viewer",
    version="2.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A powerful tool for viewing and managing image metadata",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url="https://github.com/yourusername/image-metadata-viewer",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Pillow>=10.0.0',
        'CustomTkinter>=5.0.0',
        'tkinterdnd2>=0.5.0',
        'requests>=2.31.0',
        'python-dotenv>=1.0.0'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Utilities"
    ],
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'image-metadata-viewer=imagInfo:main'
        ]
    },
)
