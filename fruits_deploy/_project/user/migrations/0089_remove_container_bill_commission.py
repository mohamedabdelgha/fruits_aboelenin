# Generated by Django 3.2 on 2024-01-24 20:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0088_container_bill_commission'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='container',
            name='bill_commission',
        ),
    ]
