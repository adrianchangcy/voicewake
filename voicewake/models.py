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

#defaults
#'any' means randomise later
#pass others to set it as default
def get_current_datetime_with_tz():
    return datetime.now().astimezone(tz=ZoneInfo('UTC'))


def get_default_country():
    #should get user's geolocation
    return Countries.objects.get_or_create(country_name='United States of America', country_name_shortened='USA')[0]


def get_default_language():
    return Languages.objects.get_or_create(country_name='English', country_name_shortened='ENG')[0]


#determine appropriate file path
def determine_event_audio_file_path_and_name(instance, filename):
    
    #FYI, no need to have separate audio and video directory
    #will always have only one or the other, not both

    #e.g.:
    #MEDIA_ROOT/talkers/year_2022/month_08/uer_7
    #no need to type out MEDIA_ROOT here, as it is determined in settings.py
    file_path = 'talkers/year_{0}/month_{1}/uer_{2}'.format(
        instance.when_created.strftime('%Y'),
        instance.when_created.strftime('%m'),
        instance.user_event_role.id
    )

    #e.g.:
    #adrian_uer_7_e_9
    new_file_name = '{0}_uer_{1}_e_{2}'.format(
        instance.user_event_role.user.username,
        instance.user_event_role.id,
        instance.id
    )

    file_extension = filename.rsplit('.', 1)[-1]

    return file_path + '/' + new_file_name + '.' + file_extension


def validate_rating(value):

    if isinstance(value, int) and value >= 1 and value <= 5:

        return True

    else:

        raise ValidationError(
            _('%(value)s is not a valid rating between 1 and 5.'),
            params={'value': value}
        )


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


class EventPurposeTranslations(models.Model):
    id = models.BigAutoField(primary_key=True)
    event_purpose = models.ForeignKey('EventPurposes', on_delete=models.CASCADE, blank=True, null=True, default=None)
    language = models.ForeignKey('Languages', on_delete=models.CASCADE, blank=True, null=True, default=None)
    translation = models.TextField()
    when_created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'voicewake'
        managed = True
        db_table = 'event_purpose_translations'


class EventPurposes(models.Model):
    id = models.BigAutoField(primary_key=True)
    event_purpose_name = models.TextField(max_length=20, unique=True)
    when_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'voicewake'
        managed = True
        db_table = 'event_purposes'

    def __str__(self):
        return self.event_purpose_name


class EventRepeatDetails(models.Model):
    #no new row if none of these are specified at form
    id = models.BigAutoField(primary_key=True)
    event = models.OneToOneField('Events', on_delete=models.CASCADE, blank=True, null=True, default=None)
    is_repeat = models.BooleanField()
    trigger_mon_to_sun = ArrayField(
        models.BooleanField(default=False),
        size=7,
        blank=True, null=True
    )
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'voicewake'
        managed = True
        db_table = 'event_repeat_details'


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
    user_event_role = models.ForeignKey(
        'UserEventRoles',
        on_delete=models.CASCADE,
        related_name='user_event_roles1',
        blank=True,
        null=True,
        default=None
    )
    event = models.ForeignKey('Events', on_delete=models.CASCADE, blank=True, null=True)
    requested_user_event_role = models.ForeignKey(
        'UserEventRoles',
        on_delete=models.CASCADE,
        related_name='user_event_roles2',
        blank=True,
        null=True,
        default=None
    )
    event_request_status = models.ForeignKey(
        EventRequestStatuses,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        default=None
    )
    payment_id = models.BigIntegerField(blank=True, null=True)  #should be FK, but until further notice
        #any initial request money offered is already a payment (to the company, to be held)
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


class EventRoomMatchReportChoices(models.Model):
    id = models.BigAutoField(primary_key=True)
    event_room_match_report_choice_name = models.TextField(max_length=100, unique=True)
    when_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'voicewake'
        managed = True
        db_table = 'event_room_match_report_choices'


class EventRoomMatchReports(models.Model):
    id = models.BigAutoField(primary_key=True)
    event_room_match = models.ForeignKey(
        'EventRoomMatches',
        on_delete=models.PROTECT,
        related_name='event_room_match_reports1',
        blank=True,
        null=True,
        default=None
    )
    reported_event_room_match = models.ForeignKey(
        'EventRoomMatches',
        on_delete=models.PROTECT,
        related_name='event_room_match_reports2',
        blank=True,
        null=True,
        default=None
    )
    event_room_match_report_choice = models.ForeignKey(
        EventRoomMatchReportChoices,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        default=None
    )
    reported_message = models.TextField()
    when_created = models.DateTimeField(auto_now_add=True)
    is_valid = models.BooleanField(blank=True, null=True)
    when_validated = models.DateTimeField(blank=True, null=True)
    validation_message = models.TextField()
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'voicewake'
        managed = True
        db_table = 'event_room_match_reports'


#a user that submits a score/message stores it in his/her own row, not the other's
class EventRoomMatches(models.Model):
    id = models.BigAutoField(primary_key=True)
    event = models.ForeignKey('Events', on_delete=models.PROTECT, blank=True, null=True, default=None)
    event_room = models.ForeignKey('EventRooms', on_delete=models.PROTECT, blank=True, null=True, default=None)
    when_created = models.DateTimeField(auto_now_add=True)
    when_left = models.DateTimeField(blank=True, null=True)

    class Meta:
        app_label = 'voicewake'
        managed = True
        db_table = 'event_room_matches'


#for best user experience, this won't be compulsory
class EventRoomMatchRatings(models.Model):
    id = models.BigAutoField(primary_key=True)
    event_room_match = models.ForeignKey(
        'EventRoomMatches',
        on_delete=models.CASCADE,
        related_name='event_room_match_ratings1'
    )
    rated_event_room_match = models.ForeignKey(
        'EventRoomMatches',
        on_delete=models.CASCADE,
        related_name='event_room_match_ratings2'
    )
    rating = models.IntegerField(default=3, validators=[validate_rating])
        #1 to 5
    message = models.TextField(blank=True, null=True, max_length=300)
    when_created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'voicewake'
        managed = True
        db_table = 'event_room_match_ratings'


class EventRooms(models.Model):
    id = models.BigAutoField(primary_key=True)
    event_room_name = models.TextField(blank=True, max_length=50)
    when_created = models.DateTimeField(auto_now_add=True)
    audio_file = models.TextField(blank=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'voicewake'
        managed = True
        db_table = 'event_rooms'


class EventStatuses(models.Model):
    id = models.BigAutoField(primary_key=True)
    event_status_name = models.TextField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    when_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'voicewake'
        managed = True
        db_table = 'event_statuses'


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
    user_event_role = models.ForeignKey('UserEventRoles', on_delete=models.CASCADE, blank=True, null=True, default=None)
    language = models.ForeignKey('Languages', on_delete=models.SET_NULL, blank=True, null=True, default=None)
    event_tone = models.ForeignKey('EventTones', on_delete=models.SET_NULL, blank=True, null=True, default=None)
    event_purpose = models.ForeignKey('EventPurposes', on_delete=models.SET_NULL, blank=True, null=True, default=None)
    event_status = models.ForeignKey(EventStatuses, on_delete=models.PROTECT, blank=True, null=True, default=None)
    event_name = models.TextField(max_length=40)
    when_trigger = models.DateTimeField(default=get_current_datetime_with_tz)
    event_message = models.TextField(blank=True)
    when_created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    when_locked = models.DateTimeField(blank=True, null=True, default=None)
        #should only have non-null when event_status is also 'locked_for_talker_choice'
    audio_file = models.FileField(blank=True, null=True, upload_to=determine_event_audio_file_path_and_name)

    class Meta:
        app_label = 'voicewake'
        managed = True
        db_table = 'events'


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


class UserEventRoles(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey('AuthUser', on_delete=models.CASCADE, blank=True, null=True, default=None)
    event_role = models.ForeignKey(EventRoles, on_delete=models.PROTECT, blank=True, null=True, default=None)
    given_ratings = ArrayField(
        models.IntegerField(default=0),
        size=5,
        blank=True, null=True
    )
    when_created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'voicewake'
        managed = True
        db_table = 'user_event_roles'


class UserFavourites(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        'AuthUser',
        on_delete=models.CASCADE,
        related_name='primary_users',
        blank=True,
        null=True,
        default=None
    )
    favourited_user = models.ForeignKey(
        'AuthUser',
        on_delete=models.CASCADE,
        related_name='secondary_users',
        blank=True,
        null=True,
        default=None
    )
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
    user = models.OneToOneField('AuthUser', on_delete=models.CASCADE, blank=True, null=True, default=None, unique=True)
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
