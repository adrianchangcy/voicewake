from django.db import models
from django.contrib.postgres.fields import ArrayField

#custom user model
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings    #AUTH_USER_MODEL, TOTP_KEY_BYTE_SIZE

#Python packages
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os
import shutil
from decimal import Decimal
import secrets
import re

#defaults
#'any' means randomise later
#pass others to set it as default
def get_current_datetime_with_tz():
    return datetime.now().astimezone(tz=ZoneInfo('UTC'))


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
        instance.user.username
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


#cannot import from services.py, perhaps due to circular dependency
def remove_all_whitespace(string_value):

    return re.sub(r'\s+', '', string_value, flags=re.UNICODE)



#custom user model
class UserManager(BaseUserManager):

    def _create_user(self, email, username, password, is_active, is_staff, is_superuser, **extra_fields):

        if email is None:

            raise ValueError('Users must have an email address.')

        email = remove_all_whitespace(email)
        email_lowercase = email.lower()

        if len(email) == 0:

            raise ValueError('Users must have an email address.')

        username_lowercase = None

        if username is not None:
            username = remove_all_whitespace(username)
            username_lowercase = username.lower()

        now = get_current_datetime_with_tz()
        totp_key = secrets.token_bytes(settings.TOTP_KEY_BYTE_SIZE)

        user = self.model(
            email=email,
            email_lowercase=email_lowercase,
            username=username,
            username_lowercase=username_lowercase,
            totp_key=totp_key,
            is_active=is_active,
            is_staff=is_staff,
            is_superuser=is_superuser,
            last_login=now,
            date_joined=now,
            **extra_fields
        )

        #FYI, set_password() falls back to set_unusable_password() when None
        #password=None for regular users
        user.set_password(password)
        user.save(using=self._db)

        #don't create UserOTP() here, as it's only needed when OTP is needed
        return user

    #for normal users, if manual, call get_user_model().objects.create_user()
    #py manage.py createsuperuser and UserCreationForm will auto-call these methods

    def create_user(self, email, **extra_fields):
        return self._create_user(email, None, None, False, False, False, **extra_fields)

    def create_superuser(self, email, username, password, **extra_fields):
        return self._create_user(email, username, password, True, True, True, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.BigAutoField(primary_key=True)
    email = models.EmailField(max_length=254, unique=True)  #preserve uppercase
    email_lowercase = models.CharField(max_length=254, unique=True) #all lowercase
    username = models.CharField(max_length=30, unique=True, null=True, blank=True, default=None) #preserve uppercase
    username_lowercase = models.CharField(max_length=30, unique=True, null=True, blank=True, default=None) #all lowercase
    totp_key = models.BinaryField()
    password = models.CharField(max_length=128) #still used for superuser
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    #email_lowercase and username_lowercase are for matching against db
    #email and username are for displaying and general usage

    #FYI, do not need unique_together for email and username, else two unique emails can have the same username, and vice versa
    #for username, string should always use '', but due to unique constraint, we must use null

    #main field for account's identifier, must also be unique
    USERNAME_FIELD = 'email'

    #should match the email field's name
    EMAIL_FIELD = 'email'

    #only for extra fields when running manage.py createsuperuser, excluding username and password
    REQUIRED_FIELDS = ['username']

    objects = UserManager()


    def save(self, *args, **kwargs):

        self.email_lowercase = self.email.lower()

        if self.username is not None:
            self.username_lowercase = self.username.lower()

        super(User, self).save(*args, **kwargs)





#delete on success or on max attempts once max attempt timeout has passed
class UserOTP(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    when_created = models.DateTimeField(auto_now_add=True)
    attempts = models.SmallIntegerField(default=0)
    last_attempted = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'voicewake'
        managed = True
        db_table = 'user_otp'


class EventLikesDislikes(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, default=None, related_name='event_requests_auth_user_1')
    requested_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, default=None, related_name='event_requests_auth_user_2')
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
    locked_for_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, default=None, related_name='event_rooms_auth_user_1')
    is_replying = models.BooleanField(blank=True, null=True, default=None)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, default=None, related_name='event_rooms_auth_user_2')
    when_created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'voicewake'
        managed = True
        db_table = 'event_rooms'


class EventToneTranslations(models.Model):
    id = models.BigAutoField(primary_key=True)
    event_tone = models.ForeignKey('EventTones', on_delete=models.CASCADE, blank=True, null=True, default=None)
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
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, default=None)
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


class UserEventRooms(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, default=None)
    event_room = models.ForeignKey('EventRooms', on_delete=models.CASCADE, null=True, default=None)
    is_seen_at_front_page = models.BooleanField(default=False)
    is_excluded_for_reply = models.BooleanField(default=False)
    when_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'voicewake'
        managed = True
        db_table = 'user_event_rooms'
        unique_together = ('user', 'event_room')


class UserFavourites(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_favourites_auth_user_1', blank=True, null=True, default=None)
    favourited_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_favourites_auth_user_2', blank=True, null=True, default=None)
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




