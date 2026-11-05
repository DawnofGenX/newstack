"""The extension build.

``extra_compile_args`` is why this file exists at all: a C extension that is not
compiled with warnings-as-errors is a C extension whose refcount bugs ship.
"""

from setuptools import Extension, setup

setup(
    ext_modules=[
        Extension(
            "{{ package_name }}._speedups",
            sources=["src/{{ package_name }}/_speedups.c"],
            extra_compile_args=["-O2", "-Wall", "-Wextra", "-Werror"],
        )
    ]
)
