"""
Use this to upload static content to S3.

TODO: consider click-ifying.
"""

import flask_s3
from .factory import create_web_app


def upload_static_files() -> None:
    """Upload static files to S3."""
    app = create_web_app()
    with app.app_context():
        flask_s3.create_all(app)


if __name__ == '__main__':
    upload_static_files()
