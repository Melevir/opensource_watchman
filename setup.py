from typing import Optional

from setuptools import setup, find_packages


package_name = 'opensource_watchman'


def get_version() -> Optional[str]:
    with open(f'{package_name}/__init__.py', 'r') as f:
        lines = f.readlines()
    for line in lines:
        if line.startswith('__version__'):
            return line.split('=')[-1].strip().strip("'")


def get_long_description() -> str:
    with open('README.md', encoding='utf8') as f:
        return f.read()


setup(
    name=package_name,
    description='Opensource repos validator.',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    classifiers=[
        'Environment :: Console',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Quality Assurance',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    packages=find_packages(),
    package_data={package_name: ['templates/*.html']},
    include_package_data=True,
    keywords='plugins',
    version=get_version(),
    author='Ilya Lebedev',
    author_email='melevir@gmail.com',
    install_requires=[
        'setuptools',
        'click>=7.1.2',
        'requests>=2.23.0',
        'Jinja2>=2.11.2',
        'pillow>=7.1.2',
        'super_mario>=0.0.1',
        'colored>=1.4.2',
    ],
    entry_points={
        'console_scripts': [
            'opensource_watchman = opensource_watchman.run:main',
        ],
    },
    url='https://github.com/Melevir/opensource_watchman',
    license='MIT',
    py_modules=[package_name],
    zip_safe=False,
)
