from django.db import migrations
from django.contrib.postgres.operations import UnaccentExtension


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        UnaccentExtension(),
    ]
