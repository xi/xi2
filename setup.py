from setuptools import setup


setup(
    name='xi2',
    version='0.0.0',
    description='a plain text language that compiles to MIDI',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Tobias Bengfort',
    author_email='tobias.bengfort@posteo.de',
    license='MIT',
    packages=['xi2'],
    entry_points={'console_scripts': [
        'xi2=xi2.__main__:main',
    ]},
)
