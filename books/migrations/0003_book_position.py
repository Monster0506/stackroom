from django.db import migrations, models


def set_initial_positions(apps, schema_editor):
    Book = apps.get_model("books", "Book")
    for i, book in enumerate(Book.objects.order_by("-date_added")):
        book.position = i
        book.save(update_fields=["position"])


class Migration(migrations.Migration):

    dependencies = [
        ("books", "0002_remove_book_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="book",
            name="position",
            field=models.PositiveIntegerField(db_index=True, default=0),
        ),
        migrations.AlterModelOptions(
            name="book",
            options={"ordering": ["position", "-date_added"]},
        ),
        migrations.RunPython(set_initial_positions, migrations.RunPython.noop),
    ]
