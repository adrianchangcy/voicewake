from django.forms import CharField, DateTimeField
from rest_framework import serializers

from .services import has_numbers_only, remove_all_whitespace
from .models import *
from django.conf import settings

import json



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class EventRolesSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventRoles
        exclude = ['when_created']


class EventTonesSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventTones
        exclude = ['when_created']


class UserVerificationOptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserVerificationOptions
        fields = ['id', 'user_verification_option_name', 'when_created']


class EventLikesDislikesSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = EventLikesDislikes
        fields = '__all__'


class GenericStatusesSerializer(serializers.ModelSerializer):
    class Meta:
        model = GenericStatuses
        exclude = ['when_created', 'last_modified']


class EventRoomsSerializer(serializers.ModelSerializer):
    generic_status = GenericStatusesSerializer()
    locked_for_user = UserSerializer()
    created_by = UserSerializer()
    class Meta:
        model = EventRooms
        fields = '__all__'



class EventsSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    event_role = EventRolesSerializer()
    event_tone = EventTonesSerializer()
    event_room = EventRoomsSerializer()
    generic_status = GenericStatusesSerializer()
    audio_volume_peaks = serializers.ListField(
        child=serializers.DecimalField(min_value=0, max_value=1, max_digits=3, decimal_places=2, coerce_to_string=False),
        min_length=20,
        max_length=20
    )

    class Meta:
        model = Events
        fields = '__all__'


#no need event_room=EventRoomsSerializer
#because we will use store into SortedEventsIntoEventRoomsSerializer.event_room, once for all related events
class EventsAndLikeDetailsSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    event_role = EventRolesSerializer()
    event_tone = EventTonesSerializer()
    event_room_id = serializers.IntegerField()
    generic_status = GenericStatusesSerializer()
    audio_volume_peaks = serializers.ListField(
        child=serializers.DecimalField(min_value=0, max_value=1, max_digits=3, decimal_places=2, coerce_to_string=False),
        min_length=20,
        max_length=20
    )
    like_count = serializers.IntegerField()
    dislike_count = serializers.IntegerField()
    is_liked_by_user = serializers.BooleanField(allow_null=True)

    class Meta:
        model = Events
        fields = ['id', 'user', 'event_role', 'event_tone', 'event_room_id', 'generic_status', 'audio_file', 'audio_volume_peaks', 'audio_duration_s', 'like_count', 'dislike_count', 'is_liked_by_user']



class GroupedEventsSerializer(serializers.Serializer):
    event_room = EventRoomsSerializer()
    originator = EventsAndLikeDetailsSerializer()
    responder = serializers.ListField(
        child=EventsAndLikeDetailsSerializer()
    )


class CreateEventLikesDislikesSerializer(serializers.Serializer):
    event_id = serializers.IntegerField()
    is_liked = serializers.BooleanField(allow_null=True)



class CreateEventsSerializer(serializers.Serializer):

    #pass only when is_originator=False
    event_room_id = serializers.IntegerField(
        required=False
    )

    #pass only when is_originator=True
    event_room_name = serializers.CharField(
        required=False,
        min_length=1,
        max_length=200, #follow EventRooms.event_room_name
    )

    event_tone_id = serializers.IntegerField()

    audio_file = serializers.FileField(
        allow_empty_file=False
    )


    def validate_audio_file(self, value):

        #ensure audio_file does not exceed max file size
        #web serve should be first line of defense at production (e.g. LimitRequestBody setting at Apache)
        #https://stackoverflow.com/questions/6195478/max-image-size-on-file-upload
        if value.size > settings.EVENT_MAX_FILE_SIZE_BYTES:

            #file is too large
            custom_error_message = "Invalid data, file is too big. Your file is %sMB, while the limit is %sMB." % (
                round(value.size / (1024 * 1024), 2),
                round(settings.EVENT_MAX_FILE_SIZE_BYTES / (1024 * 1024), 2)
            )

            raise serializers.ValidationError(custom_error_message)

        #don't do processing here, we leave it as final step at views.py
        
        return value



class HandleReplyingEventRoomsSerializer(serializers.Serializer):

    event_room_id = serializers.IntegerField()



class UsersUsernameAPISerializer(serializers.Serializer):

    username = serializers.CharField(
        min_length=1,
        max_length=30,
    )
    exists = serializers.BooleanField(
        required=False
    )


    def validate_username(self, value):

        value = remove_all_whitespace(value)

        if len(value) == 0:

            raise serializers.ValidationError('Empty username.')
        
        #disallow these usernames
        with open(os.path.join(settings.BASE_DIR, 'voicewake/static/json/bad_usernames.en.json')) as file:

            bad_usernames = json.load(file)['usernames']

            if value in bad_usernames:

                raise serializers.ValidationError('Username not allowed.')

        #either entirely letters and numbers only,
        #or start and end with letters and numbers with possible '_' and '.' in between
        #with the addition of {1,30} for condition 1, constant 120+ steps becomes 6 steps
        #if '_' or '.', cannot continue with another '_' nor '.'
        if re.match(r'(^[a-zA-Z0-9]{1,30}$)|(^[a-zA-Z0-9](_(?!(\.|_))|\.(?!(_|\.))|[a-zA-Z0-9]){0,28}[a-zA-Z0-9]$)', value) is None:

            raise serializers.ValidationError('Invalid username format.')

        return value



#used for both signing in and creating account
class UsersLogInAPISerializer(serializers.Serializer):

    #no need to do our own regex check for EmailField
    email = serializers.EmailField(max_length=254)
    otp = serializers.CharField(
        min_length=settings.TOTP_NUMBER_OF_DIGITS,
        max_length=settings.TOTP_NUMBER_OF_DIGITS,
        required=False
    )
    #BooleanField has bug where if arg is not passed and required=False,
    #it still unintentionally appears in your data with value False
    #https://github.com/encode/django-rest-framework/issues/8300
    is_requesting_new_otp = serializers.BooleanField(
        default=False
    )


    def validate_email(self, value):

        value = remove_all_whitespace(value)

        if len(value) == 0:

            raise serializers.ValidationError('Empty email.')
        
        return value


    def validate_otp(self, value):

        value = remove_all_whitespace(value)

        if len(value) != settings.TOTP_NUMBER_OF_DIGITS or has_numbers_only(value) is False:

            raise serializers.ValidationError('Invalid OTP.')

        return value
    

    def validate(self, data):

        if 'otp' in data and data['is_requesting_new_otp'] is True:

            raise serializers.ValidationError('Cannot request for new OTP while submitting OTP.')

        return data









