import re

from django.db import migrations

EMAIL = re.compile(r'[\w.+-]+@[\w-]+(?:\.[\w-]+)+')


def scrub(apps, schema_editor):
    """Older history lines named people by email ("ann@x.com joined via code ..."). Everyone in the family
    can read the history, so swap those for the person's name, and drop stored email/address values."""
    EditHistory = apps.get_model('edit_history', 'EditHistory')
    for row in EditHistory.objects.filter(change_description__contains='@').select_related('edited_by'):
        user = row.edited_by
        name = f'{user.first_name} {user.last_name}'.strip() if user else ''
        text = row.change_description
        if user and user.email:
            text = text.replace(user.email, name or 'A family member')
        text = EMAIL.sub('a family member', text)
        if text != row.change_description:
            row.change_description = text
            row.save(update_fields=['change_description'])
    EditHistory.objects.filter(field_name__in=['email', 'address']).update(old_value='', new_value='')


class Migration(migrations.Migration):
    dependencies = [('edit_history', '0002_edithistory_by_staff')]
    operations = [migrations.RunPython(scrub, migrations.RunPython.noop)]
