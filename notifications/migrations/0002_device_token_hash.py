import hashlib

from django.db import migrations, models


def populate_token_hashes(apps, schema_editor):
    DeviceToken = apps.get_model("notifications", "DeviceToken")
    database_alias = schema_editor.connection.alias
    for device_token in DeviceToken.objects.using(database_alias).all().iterator():
        device_token.token_hash = hashlib.sha256(
            device_token.token.encode("utf-8")
        ).hexdigest()
        device_token.save(update_fields=("token_hash",), using=database_alias)


class Migration(migrations.Migration):
    dependencies = [
        ("notifications", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="devicetoken",
            name="token_hash",
            field=models.CharField(editable=False, max_length=64, null=True),
        ),
        migrations.RunPython(populate_token_hashes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="devicetoken",
            name="token_hash",
            field=models.CharField(editable=False, max_length=64, unique=True),
        ),
        migrations.AlterField(
            model_name="devicetoken",
            name="token",
            field=models.CharField(max_length=512),
        ),
    ]
