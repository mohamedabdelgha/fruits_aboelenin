# Generated by Django 3.2.23 on 2024-01-06 16:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0025_containeritem_tool'),
    ]

    operations = [
        migrations.AddField(
            model_name='container',
            name='main_total_count',
            field=models.PositiveIntegerField(blank=True, default=0, null=True),
        ),
    ]
