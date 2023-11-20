from django.forms import CharField, DateTimeField
from rest_framework import serializers

from .services import has_numbers_only, remove_all_whitespace
from .models import *
from django.conf import settings

import json



class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username']



class AudioClipRolesSerializer(serializers.ModelSerializer):
    class Meta:
        model = AudioClipRoles
        exclude = ['when_created']



class AudioClipTonesSerializer(serializers.ModelSerializer):
    class Meta:
        model = AudioClipTones
        exclude = ['when_created']



class UserVerificationOptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserVerificationOptions
        fields = ['id', 'user_verification_option_name', 'when_created']



class AudioClipLikesDislikesSerializer(serializers.ModelSerializer):
    user = UsersSerializer()
    class Meta:
        model = AudioClipLikesDislikes
        fields = '__all__'



class GenericStatusesSerializer(serializers.ModelSerializer):
    class Meta:
        model = GenericStatuses
        exclude = ['when_created', 'last_modified']



#instead of when_locked, do when_locked_for_this_user on request.user basis for obscurity
class EventsSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    event_name = serializers.CharField()
    when_created = serializers.DateTimeField()
    generic_status = GenericStatusesSerializer()



class AudioClipsSerializer(serializers.ModelSerializer):
    user = UsersSerializer()
    audio_clip_role = AudioClipRolesSerializer()
    audio_clip_tone = AudioClipTonesSerializer()
    event = EventsSerializer()
    generic_status = GenericStatusesSerializer()
    audio_volume_peaks = serializers.ListField(
        child=serializers.DecimalField(min_value=0, max_value=1, max_digits=3, decimal_places=2, coerce_to_string=False),
        min_length=20,
        max_length=20
    )

    class Meta:
        model = AudioClips
        fields = '__all__'



class EventReplyQueuesSerializer(serializers.ModelSerializer):

    class Meta:
        model = EventReplyQueues
        fields = ['event_id', 'when_locked', 'is_replying']























#===============APIs=================























class TestAPISerializer(serializers.Serializer):

    val_1 = serializers.IntegerField()
    val_2 = serializers.IntegerField(required=False, default=None)



#no need event=EventsSerializer
#because we will use store into SortedAudioClipsIntoEventsSerializer.event, once for all related audio_clips
class AudioClipsAndLikeDetailsAPISerializer(serializers.ModelSerializer):
    user = UsersSerializer()
    audio_clip_role = AudioClipRolesSerializer()
    audio_clip_tone = AudioClipTonesSerializer()
    event_id = serializers.IntegerField()
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
        model = AudioClips
        fields = ['id', 'user', 'audio_clip_role', 'audio_clip_tone', 'event_id', 'generic_status', 'audio_file', 'audio_volume_peaks', 'audio_duration_s', 'like_count', 'dislike_count', 'is_liked_by_user']



class EventsAndAudioClipsAPISerializer(serializers.Serializer):
    event = EventsSerializer()
    originator = AudioClipsAndLikeDetailsAPISerializer()
    responder = serializers.ListField(
        child=AudioClipsAndLikeDetailsAPISerializer()
    )



class LockedEventsAndAudioClipsAPISerializer(serializers.Serializer):
    event = EventsSerializer()
    originator = AudioClipsAndLikeDetailsAPISerializer()
    responder = serializers.ListField(
        child=AudioClipsAndLikeDetailsAPISerializer()
    )
    event_reply_queue = EventReplyQueuesSerializer()



class CreateAudioClipLikesDislikesSerializer(serializers.Serializer):
    audio_clip_id = serializers.IntegerField()
    is_liked = serializers.BooleanField(allow_null=True)



class CreateAudioClipsAPISerializer(serializers.Serializer):

    #pass only when is_originator=False
    event_id = serializers.IntegerField(
        required=False
    )
    #pass only when is_originator=True
    event_name = serializers.CharField(
        required=False,
        min_length=1,
        max_length=200, #follow Events.event_name
    )
    audio_clip_tone_id = serializers.IntegerField(min_value=1)
    audio_file = serializers.FileField(
        allow_empty_file=False
    )


    def validate_audio_file(self, value):

        #ensure audio_file does not exceed max file size
        #web serve should be first line of defense at production (e.g. LimitRequestBody setting at Apache)
        #https://stackoverflow.com/questions/6195478/max-image-size-on-file-upload
        if value.size > settings.AUDIO_CLIP_MAX_FILE_SIZE_BYTES:

            #file is too large
            custom_error_message = "Invalid data, file is too big. Your file is %sMB, while the limit is %sMB." % (
                round(value.size / (1024 * 1024), 2),
                round(settings.AUDIO_CLIP_MAX_FILE_SIZE_BYTES / (1024 * 1024), 2)
            )

            raise serializers.ValidationError(custom_error_message)

        #don't do processing here, we leave it as final step at views.py
        
        return value



class ListEventReplyChoicesAPISerializer(serializers.Serializer):

    audio_clip_tone_id = serializers.IntegerField(required=False, default=0)
    unlock_all_locked_events = serializers.BooleanField()



class HandleReplyingEventsAPISerializer(serializers.Serializer):

    event_id = serializers.IntegerField()



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



#used for both login and sign-up
class UsersLogInSignUpAPISerializer(serializers.Serializer):

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

        if data['is_requesting_new_otp'] is True and 'otp' in data:

            raise serializers.ValidationError('Cannot request for new OTP while submitting OTP.')
        
        elif data['is_requesting_new_otp'] is False and 'otp' not in data:

            raise serializers.ValidationError('Missing OTP.')

        return data



class UserBlocksSerializer(serializers.ModelSerializer):

    blocked_user = UsersSerializer()
    is_blocked = serializers.BooleanField(default=True) #for frontend only

    class Meta:
        model = UserBlocks
        fields = ['blocked_user', 'is_blocked']



class UserBlocksAPISerializer(serializers.Serializer):

    username = serializers.CharField(min_length=1, max_length=30)
    to_block = serializers.BooleanField()



class AudioClipReportsAPISerializer(serializers.Serializer):

    reported_audio_clip_id = serializers.IntegerField()



class BrowseEventsAPISerializer(serializers.Serializer):

    #cursor_token max_length is double of usual
    username = serializers.CharField(required=False, default='', max_length=30)
    latest_or_best = serializers.CharField()
    timeframe = serializers.CharField()
    audio_clip_role_name = serializers.CharField()
    audio_clip_tone_id = serializers.IntegerField(required=False, default=None, min_value=1)
    next_or_back = serializers.CharField()
    cursor_token = serializers.CharField(required=False, default='', max_length=200)


    def validate_latest_or_best(self, value):

        if value in ['latest']:

            return value

        raise serializers.ValidationError("Accepted values not specified: latest.")


    def validate_timeframe(self, value):

        if value in ['all', 'month', 'week', 'day']:

            return value

        raise serializers.ValidationError("Accepted values not specified: all/month/week/day.")


    def validate_audio_clip_role_name(self, value):

        if value in ['originator', 'responder']:

            return value

        raise serializers.ValidationError("Accepted values not specified: originator/responder.")


    def validate_next_or_back(self, value):

        if value in ['next', 'back']:

            return value

        raise serializers.ValidationError("Accepted values not specified: next/back.")



class UserBannedAudioClipsAPISerializer(serializers.Serializer):

    #cursor_token max_length is double of usual
    username = serializers.CharField(required=False, min_length=1, max_length=30)
    next_or_back = serializers.CharField()
    cursor_token = serializers.CharField(required=False, default='', max_length=200)


    def validate_next_or_back(self, value):

        if value in ['next', 'back']:

            return value

        raise serializers.ValidationError("Accepted values not specified: next/back.")

















