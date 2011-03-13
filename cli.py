import sys

from annotator.app import app, setup_app
import annotator.model as model


def fixtures():
    acc = model.Account.get('tester')
    if acc is None:
        acc = model.Account(
            id='tester',
            username='tester',
            email='tester@annotateit.org'
            )
        acc.password = 'pass'
        acc.save()
    for x in [1,2,3]:
        anno = model.Annotation(
            account_id=acc.id,
            text=x*str(x)
            )
        anno.save()
    print 'Fixtures created (tester@annotateit.org / pass)'


if __name__ == '__main__':
    setup_app()
    action = sys.argv[1]
    if action == 'fixtures':
        fixtures()


