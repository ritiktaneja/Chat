# Generated by Django 3.0.5 on 2020-05-01 19:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat_app', '0002_change_msg_user_constraint'),
    ]

    operations = [
        migrations.RenameField(
            model_name='message',
            old_name='author',
            new_name='sender',
        ),
    ]
