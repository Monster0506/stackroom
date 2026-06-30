from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("books", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="book",
            name="status",
        ),
    ]
