import json
import logging

from .models import EditHistory

STAFF_PREFIX = 'Staff edit: '
staff_log = logging.getLogger('kinship.staff')


def log_edit(tree, entity_type, entity_id, user, description, field_name='', old_value='', new_value='',
             by_staff=False):
    """
    Add one line to the tree's edit history. `by_staff` marks a change a superuser made through staff
    edit mode: it is stored as a flag AND spelled out at the start of the description, so every
    client (including ones that only show the description) tells the tree's owner it was staff.
    """
    if by_staff and not description.startswith(STAFF_PREFIX):
        description = STAFF_PREFIX + description
    EditHistory.objects.create(
        tree=tree,
        entity_type=entity_type,
        entity_id=entity_id,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        change_description=description,
        edited_by=user,
        by_staff=by_staff,
    )


def as_json(value):
    """A readable, stable text form of a snapshot, for the old_value / new_value columns."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def log_staff_change(user, tree, action, entity, entity_id, fields=()):
    """The matching line in the server log: who, where, what kind of change, and which fields (names
    only - values live in the edit history, and private ones are never written anywhere)."""
    staff_log.info('staff_change user=%s tree=%s action=%s entity=%s id=%s fields=%s',
                   user.id, tree.id, action, entity, entity_id, ','.join(fields) or '-')
