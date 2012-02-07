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

    annotator.create_app()
    annotator.create_all()

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

    with annotator.app.test_request_context():

        print("\nCreating admin user... ", end="")

        u = User(username, email, password)

        annotator.db.session.add(u)
        annotator.db.session.commit()

        print("done.")

        print("Creating primary consumer... ", end="")

        c = Consumer(ckey)
        c.user_id = u.id

        annotator.db.session.add(c)
        annotator.db.session.commit()

        print("done.\n")

        print("Primary consumer secret: %s" % c.secret)

