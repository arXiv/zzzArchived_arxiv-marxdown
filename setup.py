"""Install arXiv marXdown app."""

from setuptools import setup, find_packages

setup(
    name='arxiv-marxdown',
    version='0.1.3',
    packages=[f'arxiv.{package}' for package
              in find_packages('arxiv')],
    zip_safe=False,
    install_requires=[
        'arxiv-base==0.14.3',
        'arxiv-auth==0.2.3',
        'flask==1.0.2',
        'bleach==3.1.0',
        'unidecode==1.0.23',
        'python-dateutil',
        'markdown==2.6.11',
        'whoosh==2.7.4',
        'uwsgi==2.0.18',
        'python-frontmatter==0.4.5',
        'Pygments==2.3.1',
        'flask-s3==0.3.3',
        'mypy_extensions==0.4.1',
        'gitpython==2.1.11',
        'py-gfm==0.1.4',
        'pyyaml==4.2b4'
    ],
    include_package_data=True
)
