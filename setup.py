from setuptools import setup

setup(
    name='ldcp',
    version='1.0.0',
    description='Bundle dynamic Linux executables with their libraries to make them as portable as static executables',
    license='Unlicense',
    entry_points=dict(console_scripts=['ldcp=ldcp:main']),
)
