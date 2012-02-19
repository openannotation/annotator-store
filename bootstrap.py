from __future__ import print_function

from getpass import getpass
import readline
import sys

import annotator
from annotator.model import Consumer, User

if __name__ == '__main__':
    r = raw_input("This program will perform initial setup of the annotation \n"
                  "store, and create the required admin accounts. Proceed? [Y/n] ")

    if r and r[0] in ['n', 'N']:
        sys.exit(1)

    print("\nCreating SQLite database and ElasticSearch indices... ", end="")

    app = annotator.create_app()
    annotator.create_all(app)

    print("done.\n")

    username = raw_input("Admin username [admin]: ").strip()
    if not username:
        username = 'admin'

    email = ''
    while not email:
        email = raw_input("Admin email: ").strip()

    password = ''
    while not password:
        password = getpass("Admin password: ")

    ckey = raw_input("Primary consumer key [annotateit]: ").strip()
    if not ckey:
        ckey = 'annotateit'

    with app.test_request_context():
        db = app.extensions['sqlalchemy'].db

        print("\nCreating admin user... ", end="")

        u = User(username, email, password)

        db.session.add(u)
        db.session.commit()

        print("done.")

        print("Creating primary consumer... ", end="")

        c = Consumer(ckey)
        c.user_id = u.id

        db.session.add(c)
        db.session.commit()

        print("done.\n")

        print("Primary consumer secret: %s" % c.secret)

