# Generated by Django 5.1.5 on 2025-02-09 10:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pejapp", "0002_remove_profile_image_profile_display_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="post",
            name="display_name",
            field=models.CharField(default="Anonymous", max_length=100),
        ),
    ]
