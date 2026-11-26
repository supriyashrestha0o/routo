import django.db.models.deletion
from django.db import migrations, models


def remove_legacy_journeyless_reviews(apps, schema_editor):
    """Remove reviews that cannot be tied to a valid completed journey.

    Legacy journey-less reviews cannot satisfy the participation rules and
    cannot be migrated to a journey safely. The current database is empty; if
    any legacy rows exist, they are deliberately deleted before journey is
    changed to NOT NULL.
    """
    Review = apps.get_model("reviews", "Review")
    database_alias = schema_editor.connection.alias
    Review.objects.using(database_alias).filter(journey__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("reviews", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            remove_legacy_journeyless_reviews,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="review",
            name="journey",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="reviews",
                to="journeys.journey",
            ),
        ),
        migrations.AddConstraint(
            model_name="review",
            constraint=models.CheckConstraint(
                condition=models.Q(("reviewer", models.F("reviewed_user")), _negated=True),
                name="review_no_self_review",
            ),
        ),
    ]
