from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('edit_history', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='edithistory',
            name='by_staff',
            field=models.BooleanField(
                default=False,
                help_text='True when a superuser made this change through the staff edit mode.',
            ),
        ),
    ]
