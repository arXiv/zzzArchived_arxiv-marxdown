"""Install arXiv marXdown app."""

from setuptools import setup, find_packages

setup(
    name='arxiv-marxdown',
    version='0.2.5.post1',
    packages=[f'arxiv.{package}' for package
              in find_packages('arxiv')],
    zip_safe=False,
    install_requires=[
        'arxiv-base==0.17.4.post2',
        'arxiv-auth==0.4.2rc1',
        'flask==1.0.2',
        'bleach==3.3.0',
        'unidecode==1.0.23',
        'python-dateutil',
        'markdown==2.6.11',
        'whoosh==2.7.4',
        'uwsgi==2.0.18',
        'python-frontmatter==0.4.5',
        'flask-s3==0.3.3',
        'gitpython==2.1.11',
        'py-gfm==0.1.4',
        'pyyaml==5.1b1',
        'gitdb2==2.0.6',
        'mypy_extensions==0.4.3',
        'Pygments==2.3.1'
    ],
    include_package_data=True
)
