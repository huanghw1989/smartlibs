from setuptools import setup, find_packages


NAME = 'smartlibs'
VERSION = '0.1.9'
DESCRIPTION = 'Smart Platforms Libs'
EMAIL = 'huanghongwu@sipuai.com'
AUTHOR = 'huanghongwu'
REQUIRES_PYTHON = '>=3.5.0'

REQUIRED = [
    'debugpy',
    'fire',
    'pyyaml',
    'requests',
    # auto_tasks
    'redis',
    'nvidia-ml-py',
    # aio
    # 'asyncio_redis'
]

EXTRAS_REQUIRE = {
    'kafka': [
        'confluent-kafka',
    ]
}

auto_tasks_package_data = {
    "auto_tasks": ['*.yml']
}

setup(
    name=NAME,
    version=VERSION,
    author=AUTHOR,
    author_email=EMAIL,
    packages=find_packages(
        exclude=['tests', 'tests.*']
    ),
    namespace_packages=['smart', 'auto_tasks'],
    python_requires=REQUIRES_PYTHON,
    install_requires=REQUIRED,
    extras_require=EXTRAS_REQUIRE,
    package_data={
        **auto_tasks_package_data,
    },
    entry_points={
        'console_scripts': [
            'smart_auto = smart.auto.run:cmd_ep',
            'smart_auto_debug = smart.auto.run_debug:cmd_ep',
            'smart_aaas = smart.aaas.run:cmd_ep',
            'smart_aaas_debug = smart.aaas.run_debug:cmd_ep'
        ]
    }
)