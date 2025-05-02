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



def config_param_operations():

    #be consistent with booleans
        #0 for FALSE, 1 for TRUE
    #this is an alternative to using .conf at dev or specifying parameters at AWS

    with connection.cursor() as cursor:

        #this allows trigger functions to exit early
        #with 250000 rows, performance is 1s slower to 3s faster compared to completely disabling trigger at table
        #useful in bulk operations, by overriding param at only current transaction via SET LOCAL, e.g.:
            # with transaction.atomic():
                # with connection.cursor() as cursor:
                    # cursor.execute('''SET LOCAL voicewake.skip_trigger_audio_clip_likes_dislikes = 1;''')
                    # AudioClipLikesDislikes.objects.filter(audio_clip=audio_clip).delete()
        #how to check if conf param override is truly occuring only within the transaction
            # check_sql = "SELECT NULLIF(current_setting('voicewake.skip_trigger_audio_clip_likes_dislikes'), NULL);"
            # cursor.execute(check_sql)
            # skip_trigger = int(cursor.fetchone()[0])
        cursor.execute(
            '''
                ALTER SYSTEM SET voicewake.skip_trigger_audio_clip_likes_dislikes TO 0;
            '''
        )

        #ensure this is appended as last operation
        #pg_reload_conf() ensures changes to params are made
        cursor.execute(
            '''
                SELECT pg_reload_conf();
            '''
        )

config_param_operations()



#the "OLD.is_liked IS FALSE AND NEW.is_liked IS TRUE" and vice versa part is important
#to protect against race condition redundancy, i.e. multiple requests with same action
#for like_ratio, must cast any one value with ::float to prevent rounding off to int, i.e. always 0.00 or 1.00
custom_function_handle_audio_clip_likes_dislikes_count = '''
    CREATE OR REPLACE FUNCTION handle_audio_clip_likes_dislikes_count() RETURNS TRIGGER AS $$
        BEGIN
            IF (current_setting('voicewake.skip_trigger_audio_clip_likes_dislikes')::integer = 0) THEN

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

                    /*
                    *only run UPDATE when is_liked will be changed, to prevent duplicate UPDATEs from having duplicated effects
                    */

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
                    *use COALESCE + NULLIF trick to solve "division by 0" error
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
            END IF;
            RETURN NEW;
        END;
    $$ LANGUAGE plpgsql VOLATILE;
'''

custom_trigger_audio_clip_likes_dislikes = '''
    CREATE OR REPLACE TRIGGER trigger_audio_clip_likes_dislikes
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