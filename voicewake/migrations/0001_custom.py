#steps:
    #perform your normal makemigrations -->
    #create your custom migration file at ./migrations/custom/... -->
    #add the makemigrations file to the dependencies list at the bottom of your custom migration file -->
    #copy the custom migration file from ./migrations/custom/myfile to ./migrations
    #migrate

#possible better step, but worse separation between auto-generated and custom:
    #do makemigrations --> directly edit the file --> migrate

from django.db import migrations, connection
import os
import json
from django.conf import settings
from django.contrib.auth import get_user_model

#this isn't found at our models.py
from django.contrib.auth.models import Group



#expect args (apps, schema_editor) from migrations.RunPython
def fill_necessary_data(apps, schema_editor):

    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    app_name = "voicewake"

    AudioClipTones = apps.get_model(app_name, "AudioClipTones")
    GenericStatuses = apps.get_model(app_name, "GenericStatuses")
    AudioClipRoles = apps.get_model(app_name, "AudioClipRoles")

    #Group
    Group.objects.create(name="regular")

    #AudioClipTones
    with open(os.path.join(settings.BASE_DIR, 'static/voicewake/json/data_emojis_final.json'), encoding="utf8") as file:

        emojis = json.load(file)
        emojis = emojis.items()

        #store for bulk_create
        new_rows = []

        for row in emojis:

            (key, symbol) = row

            new_rows.append(
                AudioClipTones(
                    audio_clip_tone_slug=key.replace("_", "-"),
                    audio_clip_tone_name=key.replace("_"," "),
                    audio_clip_tone_symbol=symbol,
                )
            )

        #bulk_create
        AudioClipTones.objects.bulk_create(
            new_rows,
            ignore_conflicts=True
        )

        file.close()

    #GenericStatuses
    GenericStatuses.objects.bulk_create(
        [
            GenericStatuses(generic_status_name='ok'),
            GenericStatuses(generic_status_name='deleted'),
            GenericStatuses(generic_status_name='incomplete'),
            GenericStatuses(generic_status_name='completed'),
            GenericStatuses(generic_status_name='processing'),
            GenericStatuses(generic_status_name='processing_max_attempts_reached'),
            GenericStatuses(generic_status_name='processing_overdue'),
        ],
        ignore_conflicts=True
    )

    AudioClipRoles.objects.bulk_create(
        [
            AudioClipRoles(audio_clip_role_name='originator'),
            AudioClipRoles(audio_clip_role_name='responder')
        ],
        ignore_conflicts=True
    )

    #ensure admin account exists
    #this is a short-term solution, as superusers should also have proper password
        #specifying password here or at .env is improper if superusers should have access to only their account
    #for long-term solution:
        #at frontend, enter username, check is_superuser, prompt password, then prompt TOTP
            #better to prompt password first so no DoS
            #once done, update code that refers to this account, to check for .is_superuser instead
    get_user_model().objects.create_superuser(email='adrianchangcy@gmail.com', username='AdrianC', password=None)

    print("\nFinished populating db with necessary data.")






class Migration(migrations.Migration):

    dependencies = [
        ('voicewake', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(fill_necessary_data),
    ]