# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = True` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
# from django.contrib.auth.models import PermissionsMixin

#Python packages
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os
import shutil
from decimal import Decimal

#defaults
#'any' means randomise later
#pass others to set it as default
def get_current_datetime_with_tz():
    return datetime.now().astimezone(tz=ZoneInfo('UTC'))


def get_default_country():
    #should get user's geolocation
    return Countries.objects.get_or_create(country_name='United States of America', country_name_shortened='USA')[0].id


def get_default_language():
    return Languages.objects.get_or_create(country_name='English', country_name_shortened='ENG')[0].id


#determine appropriate file path
def determine_event_audio_file_path_and_name(instance, filename):
    
    #FYI, no need to have separate audio and video directory
    #will always have only one or the other, not both

    #e.g.:
    #MEDIA_ROOT/recordings/year_2022/month_08/day_01/username
    #no need to type out MEDIA_ROOT here, as it is determined in settings.py
    file_path = 'events/year_{0}/month_{1}/day_{2}/{3}'.format(
        instance.when_created.strftime('%Y'),
        instance.when_created.strftime('%m'),
        instance.when_created.strftime('%d'),
        instance.created_by.username
    )

    #e.g.:
    #e_9
    new_file_name = 'e_{0}'.format(
        instance.id
    )

    file_extension = filename.rsplit('.', 1)[-1]

    return file_path + '/' + new_file_name + '.' + file_extension


def get_default_generic_status():
    return GenericStatuses.objects.get_or_create(generic_status_name='ok')[0].id


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        app_label = 'voicewake'
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, on_delete=models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', on_delete=models.DO_NOTHING)

    class Meta:
        app_label = 'voicewake'
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', on_delete=models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        app_label = 'voicewake'
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        app_label = 'voicewake'
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, on_delete=models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, on_delete=models.DO_NOTHING)

    class Meta:
        app_label = 'voicewake'
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, on_delete=models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, on_delete=models.DO_NOTHING)

    class Meta:
        app_label = 'voicewake'
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class Countries(models.Model):
    id = models.BigAutoField(primary_key=True)
    country_name = models.TextField(unique=True, max_length=30)
    country_name_shortened = models.TextField(blank=True, null=True, unique=True, max_length=10)
    when_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'voicewake'
        managed = True
        db_table = 'countries'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', on_delete=models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, on_delete=models.DO_NOTHING)

    class Meta:
        app_label = 'voicewake'
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        app_label = 'voicewake'
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        app_label = 'voicewake'
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        app_label = 'voicewake'
        managed = False
        db_table = 'django_session'


class EventLikesDislikes(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey('AuthUser', on_delete=models.CASCADE)
    event = models.ForeignKey('Events', on_delete=models.CASCADE)
    is_liked = models.BooleanField()
    when_created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'voicewake'
        managed = True
        db_table = 'event_likes_dislikes'


class EventRequestStatuses(models.Model):
    id = models.BigAutoField(primary_key=True)
    event_request_status_name = models.TextField(max_length=30, unique=True)
    description = models.TextField(blank=True)
    when_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'voicewake'
        managed = True
        db_table = 'event_request_statuses'


class EventRequests(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey('AuthUser', on_delete=models.CASCADE, null=True, default=None, related_name='event_requests_auth_user_1')
    requested_user = models.ForeignKey('AuthUser', on_delete=models.CASCADE, null=True, default=None, related_name='event_requests_auth_user_2')
    event_room = models.ForeignKey('EventRooms', on_delete=models.PROTECT, blank=True, null=True, default=None)
    event_request_status = models.ForeignKey('EventRequestStatuses', on_delete=models.PROTECT, blank=True, null=True, default=None)
    when_created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'voicewake'
        managed = True
        db_table = 'event_requests'


class EventRoles(models.Model):
    id = models.BigAutoField(primary_key=True)
    event_role_name = models.TextField(max_length=20, unique=True)
    when_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'voicewake'
        managed = True
        db_table = 'event_roles'


class EventRooms(models.Model):
    id = models.BigAutoField(primary_key=True)
    event_room_name = models.TextField(max_length=200, default='-') #ensure default is never used
    generic_status = models.ForeignKey('GenericStatuses', on_delete=models.PROTECT, default=get_default_generic_status)
    when_locked = models.DateTimeField(blank=True, null=True, default=None)
    locked_for_user = models.ForeignKey('AuthUser', on_delete=models.SET_NULL, blank=True, null=True, default=None, related_name='event_rooms_auth_user_1')
    is_replying = models.BooleanField(blank=True, null=True, default=None)
    created_by = models.ForeignKey('AuthUser', on_delete=models.CASCADE, blank=True, null=True, default=None, related_name='event_rooms_auth_user_2')
    when_created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'voicewake'
        managed = True
        db_table = 'event_rooms'


class EventToneTranslations(models.Model):
    id = models.BigAutoField(primary_key=True)
    event_tone = models.ForeignKey('EventTones', on_delete=models.CASCADE, blank=True, null=True, default=None)
    language = models.ForeignKey('Languages', on_delete=models.CASCADE, blank=True, null=True, default=None)
    translation = models.TextField()
    when_created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'voicewake'
        managed = True
        db_table = 'event_tone_translations'


class EventTones(models.Model):
    id = models.BigAutoField(primary_key=True)
    event_tone_name = models.TextField(max_length=50, unique=True)
    event_tone_symbol = models.TextField(max_length=50, unique=True)
    when_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'voicewake'
        managed = True
        db_table = 'event_tones'

    def __str__(self):
        return self.event_tone_name


class Events(models.Model):
    #when language/tone/purpose is null, interpret as 'any' later
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey('AuthUser', on_delete=models.CASCADE, null=True, default=None)
    event_role = models.ForeignKey('EventRoles', on_delete=models.PROTECT, blank=True, null=True, default=None)
    event_tone = models.ForeignKey('EventTones', on_delete=models.SET_NULL, blank=True, null=True, default=None)
    event_room = models.ForeignKey('EventRooms', on_delete=models.CASCADE, null=True, default=None)
    generic_status = models.ForeignKey('GenericStatuses', on_delete=models.PROTECT, default=get_default_generic_status)
    audio_file = models.FileField(blank=True, null=True, upload_to=determine_event_audio_file_path_and_name)
    audio_file_seconds = models.DecimalField(default=0, max_digits=6, decimal_places=2)
    audio_volume_peaks = ArrayField(
        models.DecimalField(default=0, max_digits=3, decimal_places=2), #0 to 0.49 to 1
        size=20,    #if size changes, change at get_default_audio_volume_peaks too
        null=True,
        default=None
    )
    when_created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'voicewake'
        managed = True
        db_table = 'events'


class GenericStatuses(models.Model):
    id = models.BigAutoField(primary_key=True)
    generic_status_name = models.TextField(max_length=200, unique=True)
    when_created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'voicewake'
        managed = True
        db_table = 'generic_statuses'


class Languages(models.Model):
    id = models.BigAutoField(primary_key=True)
    language_name = models.TextField(max_length=20, unique=True)
    language_name_shortened = models.TextField(blank=True, max_length=10, unique=True)
        #when False, means for fun
    when_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'voicewake'
        managed = True
        db_table = 'languages'

    def __str__(self):
        return self.language_name


class UserEventRooms(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey('AuthUser', on_delete=models.CASCADE, null=True, default=None)
    event_room = models.ForeignKey('EventRooms', on_delete=models.CASCADE, null=True, default=None)
    is_seen_at_front_page = models.BooleanField()
    is_excluded_for_reply = models.BooleanField()
    when_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'voicewake'
        managed = True
        db_table = 'user_event_rooms'


class UserFavourites(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey('AuthUser', on_delete=models.CASCADE, related_name='user_favourites_auth_user_1', blank=True, null=True, default=None)
    favourited_user = models.ForeignKey('AuthUser', on_delete=models.CASCADE, related_name='user_favourites_auth_user_2', blank=True, null=True, default=None)
    when_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'voicewake'
        managed = True
        db_table = 'user_favourites'


class UserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_permission_name = models.TextField()
    when_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'voicewake'
        managed = True
        db_table = 'user_permissions'


class UserVerificationOptions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_verification_option_name = models.TextField(max_length=20, unique=True)
    when_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'voicewake'
        managed = True
        db_table = 'user_verification_options'


class UserVerificationStatuses(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_verification_status_name = models.TextField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    when_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'voicewake'
        managed = True
        db_table = 'user_verification_statuses'


class UserDetails(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField('AuthUser', on_delete=models.CASCADE, unique=True)
    country = models.ForeignKey('Countries', on_delete=models.SET(get_default_country), blank=True, null=True, default=None)
    language = models.ForeignKey('Languages', on_delete=models.SET(get_default_language), blank=True, null=True, default=None)
    user_display_name = models.TextField(max_length=20)
    user_birthdate = models.DateField()
    when_created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    utc_minute_difference= models.SmallIntegerField(default=0)

    class Meta:
        app_label = 'voicewake'
        managed = True
        db_table = 'user_details'
