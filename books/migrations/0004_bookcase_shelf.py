import django.db.models.deletion
from django.db import migrations, models


def create_default_case_and_shelf(apps, schema_editor):
    Bookcase = apps.get_model("books", "Bookcase")
    Shelf = apps.get_model("books", "Shelf")
    Book = apps.get_model("books", "Book")

    if not Book.objects.exists():
        return

    case = Bookcase.objects.create(name="Case 1", position=0)
    shelf = Shelf.objects.create(bookcase=case, name="Shelf 1", position=0)
    Book.objects.update(shelf=shelf)


class Migration(migrations.Migration):

    dependencies = [
        ("books", "0003_book_position"),
    ]

    operations = [
        migrations.CreateModel(
            name="Bookcase",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(blank=True, max_length=200)),
                ("position", models.PositiveIntegerField(db_index=True, default=0)),
            ],
            options={
                "ordering": ["position"],
            },
        ),
        migrations.CreateModel(
            name="Shelf",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(blank=True, max_length=200)),
                ("position", models.PositiveIntegerField(db_index=True, default=0)),
                (
                    "bookcase",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="shelves",
                        to="books.bookcase",
                    ),
                ),
            ],
            options={
                "ordering": ["position"],
            },
        ),
        migrations.AddField(
            model_name="book",
            name="shelf",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="books",
                to="books.shelf",
            ),
        ),
        migrations.RunPython(create_default_case_and_shelf, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="book",
            name="shelf",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="books",
                to="books.shelf",
            ),
        ),
    ]
