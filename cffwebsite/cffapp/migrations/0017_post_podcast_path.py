# Generated by Django 4.2.3 on 2023-08-08 15:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cffapp', '0016_remove_post_img_post_img_path'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='podcast_path',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]