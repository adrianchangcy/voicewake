#steps:
    #perform your normal makemigrations -->
    #create your custom migration file at ./migrations/custom/... -->
    #add the makemigrations file to the dependencies list at the bottom of your custom migration file -->
    #copy the custom migration file from ./migrations/custom/myfile to ./migrations
    #migrate

#possible better step, but worse separation between auto-generated and custom:
    #do makemigrations --> directly edit the file --> migrate

from django.db import migrations
import os
import json
from django.conf import settings

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

    print("\nFinished populating db with necessary data.")


#the "OLD.is_liked IS FALSE AND NEW.is_liked IS TRUE" and vice versa part is important
#to protect against race condition redundancy, i.e. multiple requests with same action
#for like_ratio, must cast any one value with ::float to prevent rounding off to int, i.e. always 0.00 or 1.00
custom_function_handle_audio_clip_likes_dislikes_count = '''
    CREATE OR REPLACE FUNCTION handle_audio_clip_likes_dislikes_count() RETURNS TRIGGER AS $$
        BEGIN
            IF (TG_OP = 'INSERT') THEN

                IF (NEW.is_liked IS TRUE) THEN

                    UPDATE audio_clips
                    SET like_count = like_count + 1,
					like_ratio = (like_count + 1)::float / (like_count + dislike_count + 1)
                    WHERE id = NEW.audio_clip_id
                    ;

                ELSIF (NEW.is_liked IS FALSE) THEN

                    UPDATE audio_clips
                    SET dislike_count = dislike_count + 1,
					like_ratio = like_count::float / (like_count + dislike_count + 1)
                    WHERE id = NEW.audio_clip_id
                    ;

                END IF;
                RETURN NEW;

            ELSIF (TG_OP = 'UPDATE') THEN

                IF (OLD.is_liked IS FALSE AND NEW.is_liked IS TRUE) THEN

                    UPDATE audio_clips
                    SET like_count = like_count + 1,
                    dislike_count = dislike_count - 1,
					like_ratio = (like_count + 1)::float / (like_count + dislike_count)
                    WHERE id = NEW.audio_clip_id
                    ;

                ELSIF (OLD.is_liked IS TRUE AND NEW.is_liked IS FALSE) THEN

                    UPDATE audio_clips
                    SET like_count = like_count - 1,
                    dislike_count = dislike_count + 1,
					like_ratio = (like_count - 1)::float / (like_count + dislike_count)
                    WHERE id = NEW.audio_clip_id
                    ;

                END IF;
                RETURN NEW;

            ELSIF (TG_OP = 'DELETE') THEN

                /*
                *we use COALESCE + NULLIF trick to solve "division by 0" error
                */

                IF (OLD.is_liked IS TRUE) THEN

                    UPDATE audio_clips
                    SET like_count = like_count - 1,
					like_ratio = (like_count - 1)::float / (
                        COALESCE(
                            NULLIF((like_count + dislike_count - 1), 0),
                            1
                        )
                    )
                    WHERE id = OLD.audio_clip_id
                    ;

                ELSIF (OLD.is_liked IS FALSE) THEN

                    UPDATE audio_clips
                    SET dislike_count = dislike_count - 1,
					like_ratio = like_count::float / (
                        COALESCE(
                            NULLIF((like_count + dislike_count - 1), 0),
                            1
                        )
                    )
                    WHERE id = OLD.audio_clip_id
                    ;

                END IF;

                RETURN OLD;

            END IF;
            RETURN NULL;
        END;
    $$ LANGUAGE plpgsql VOLATILE;
'''

custom_trigger_audio_clip_likes_dislikes = '''
    CREATE TRIGGER trigger_audio_clip_likes_dislikes
    AFTER INSERT
    OR UPDATE OF is_liked 
    OR DELETE
    ON audio_clip_likes_dislikes
    FOR EACH ROW
    EXECUTE FUNCTION handle_audio_clip_likes_dislikes_count();
'''



class Migration(migrations.Migration):

    dependencies = [
        ('voicewake', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(custom_function_handle_audio_clip_likes_dislikes_count),
        migrations.RunSQL(custom_trigger_audio_clip_likes_dislikes),
        migrations.RunPython(fill_necessary_data),
    ]