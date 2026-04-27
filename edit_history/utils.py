from .models import EditHistory


def log_edit(tree, entity_type, entity_id, user, description, field_name='', old_value='', new_value=''):
    EditHistory.objects.create(
        tree=tree,
        entity_type=entity_type,
        entity_id=entity_id,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        change_description=description,
        edited_by=user,
    )
