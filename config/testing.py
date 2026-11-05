"""Small helpers shared by the API tests."""
from rest_framework.test import APIClient

from family_trees.models import FamilyTree, TreeMember
from users.models import User
from users.views import get_tokens_for_user


def make_user(name):
    return User.objects.create_user(
        email=f'{name}@example.com', google_id=f'g-{name}', first_name=name.title(),
        phone='555-0100', address=f'{name} street',
    )


def client_for(user):
    """An API client that sends a real JWT, because the views read request.auth.payload."""
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {get_tokens_for_user(user)["access"]}')
    return client


def make_tree(owner, name='Tree', **extra):
    tree = FamilyTree.objects.create(owner=owner, tree_name=name, **extra)
    TreeMember.objects.create(tree=tree, user=owner, role='owner')
    return tree


def join(tree, user):
    return TreeMember.objects.create(tree=tree, user=user, role='member')
