#Django
from django.forms import CharField, DateTimeField
from rest_framework import serializers
from typing import Literal

#py
import json

#app
from .models import *
from django.conf import settings



#voicewake.services needs voicewake.serializers
#avoiding circular import error
#easier to put needed .services code here than the other way around

def has_numbers_only(string_value):

    return re.match(r'^[0-9]+$', string_value) is not None



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
    event_id = serializers.IntegerField()
    generic_status = GenericStatusesSerializer()
    audio_volume_peaks = serializers.ListField(
        child=serializers.DecimalField(min_value=0, max_value=1, max_digits=3, decimal_places=2, coerce_to_string=False),
        min_length=20,
        max_length=20
    )
    audio_file = serializers.SerializerMethodField()

    def get_audio_file(self, object):
        if settings.USE_S3 is True:
            return settings.MEDIA_URL + str(object.audio_file)
        return '{0}{1}{2}'.format(settings.BASE_URL, settings.MEDIA_URL, str(object.audio_file))

    class Meta:
        model = AudioClips
        fields = ['id', 'user', 'audio_clip_role', 'audio_clip_tone', 'event_id', 'generic_status', 'audio_file', 'audio_volume_peaks', 'audio_duration_s']



class EventReplyQueuesSerializer(serializers.ModelSerializer):

    class Meta:
        model = EventReplyQueues
        fields = ['event_id', 'when_locked', 'is_replying']



class UserBlocksSerializer(serializers.ModelSerializer):

    blocked_user = UsersSerializer()
    is_blocked = serializers.BooleanField(default=True) #for frontend only

    class Meta:
        model = UserBlocks
        fields = ['blocked_user', 'is_blocked']




















#===============APIs=================























class TestAPISerializer(serializers.Serializer):

    val_1 = serializers.CharField(trim_whitespace=True, default='')
    val_2 = serializers.IntegerField(required=False, default=None)

    #see what CharField(trim_whitespace=True) removes
    #see if validate_() runs when required=False

    def validate_val_2(self, value):

        print('not required, but still validated')
        return value


    def validate(self, data):

        return data



#no need event=EventsSerializer
#because we will use store into SortedAudioClipsIntoEventsSerializer.event, once for all related audio_clips
class AudioClipsAndLikeDetailsAPISerializer(AudioClipsSerializer):
    like_count = serializers.IntegerField()
    dislike_count = serializers.IntegerField()
    is_liked_by_user = serializers.BooleanField(allow_null=True, default=None)

    class Meta(AudioClipsSerializer.Meta):
        fields = AudioClipsSerializer.Meta.fields + ['like_count', 'dislike_count', 'is_liked_by_user']



class EventsAndAudioClipsAPISerializer(serializers.Serializer):
    event = EventsSerializer()
    originator = serializers.ListField(
        child=AudioClipsAndLikeDetailsAPISerializer()
    )
    responder = serializers.ListField(
        child=AudioClipsAndLikeDetailsAPISerializer()
    )



class LockedEventsAndAudioClipsAPISerializer(serializers.Serializer):
    event = EventsSerializer()
    originator = serializers.ListField(
        child=AudioClipsAndLikeDetailsAPISerializer()
    )
    responder = serializers.ListField(
        child=AudioClipsAndLikeDetailsAPISerializer()
    )
    event_reply_queue = EventReplyQueuesSerializer()



class CreateAudioClipLikesDislikesSerializer(serializers.Serializer):
    audio_clip_id = serializers.IntegerField()
    is_liked = serializers.BooleanField(allow_null=True)



class CreateAudioClips_Upload_APISerializer(serializers.Serializer):

    #pass only when is_originator=True
    event_name = serializers.CharField(
        required=False,
        trim_whitespace=True,
        min_length=1,
        max_length=200, #follow Events.event_name
    )
    #pass only when is_originator=False
    event_id = serializers.IntegerField(
        required=False,
        min_value=1,
    )
    audio_clip_tone_id = serializers.IntegerField(min_value=1,)
    #this is to keep source file extension as-is in unprocessed s3
    recorded_file_extension = serializers.CharField(trim_whitespace=True, min_length=3, max_length=4)


    def validate_recorded_file_extension(self, value):

        #depends on what we asked RecordRTC to record in

        if value not in settings.AUDIO_CLIP_UNPROCESSED_FILE_TYPES:

            raise serializers.ValidationError(
                "Extension '" + value + "' is not one of: " + str(settings.AUDIO_CLIP_UNPROCESSED_FILE_TYPES)
            )

        return value


    def validate(self, data):

        audio_clip_role_name:Literal['originator', 'responder'] = self.context.get('audio_clip_role_name')

        if audio_clip_role_name not in ['originator', 'responder']:

            raise serializers.ValidationError("audio_clip_role_name is missing from self.context.")

        #FYI, if no arg passed and default= is specified,
        #it will be the "passed value" during required=False

        #check for required fields per-context

        if audio_clip_role_name == 'originator' and 'event_name' not in data:

            raise serializers.ValidationError("event_name was not passed.")

        if audio_clip_role_name == 'responder' and 'event_id' not in data:

            raise serializers.ValidationError("event_id was not passed.")

        return data



class CreateAudioClips_Upload_RegenerateURL_APISerializer(serializers.Serializer):
    audio_clip_id = serializers.IntegerField(min_value=1,)



class CreateAudioClips_Process_APISerializer(serializers.Serializer):
    audio_clip_id = serializers.IntegerField(min_value=1,)



class AWSLambdaNormaliseAudioClipsAPISerializer(serializers.Serializer):
    lambda_status_code = serializers.IntegerField()
    lambda_message = serializers.CharField(min_length=0, max_length=300)
    audio_volume_peaks = serializers.ListField(
        child=serializers.DecimalField(min_value=0, max_value=1, max_digits=3, decimal_places=2, coerce_to_string=False),
        min_length=20,
        max_length=20
    )
    audio_duration_s = serializers.IntegerField()



class ListEventReplyChoicesAPISerializer(serializers.Serializer):

    audio_clip_tone_id = serializers.IntegerField(required=False, default=None, min_value=1)
    unlock_all_locked_events = serializers.BooleanField()



class HandleReplyingEventsAPISerializer(serializers.Serializer):

    event_id = serializers.IntegerField(min_value=1,)



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
        with open(os.path.join(settings.BASE_DIR, 'static/voicewake/json/bad_usernames.en.json')) as file:

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



class AudioClipReportsAPISerializer(serializers.Serializer):

    audio_clip_id = serializers.IntegerField()



class BrowseEventsAPISerializer(serializers.Serializer):

    #cursor_token max_length is double of usual
    username = serializers.CharField(required=False, default='', max_length=30)
    latest_or_best = serializers.CharField()
    timeframe = serializers.CharField()
    audio_clip_role_name = serializers.CharField()
    audio_clip_tone_id = serializers.IntegerField(required=False, default=None, min_value=1)
    next_or_back = serializers.CharField()
    likes_or_dislikes = serializers.CharField(required=False, default='', max_length=8)
    cursor_token = serializers.CharField(required=False, default='', max_length=200)


    def validate_username(self, value):

        value = remove_all_whitespace(value)

        if len(value) == 0:

            return value
        
        #disallow these usernames
        with open(os.path.join(settings.BASE_DIR, 'static/voicewake/json/bad_usernames.en.json')) as file:

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


    def validate_likes_or_dislikes(self, value):

        if value == '' or value in ['likes', 'dislikes']:

            return value

        raise serializers.ValidationError("Accepted values not specified: likes/dislikes.")


    def validate(self, data):

        if data['likes_or_dislikes'] != '' and len(data['username']) == 0:

            raise serializers.ValidationError(
                "For likes/dislikes, you can only view by per-user basis. Please specify a username."
            )

        return data



class CreateUserBlocksAPISerializer(serializers.Serializer):

    username = serializers.CharField(min_length=1, max_length=30)
    to_block = serializers.BooleanField()



class GetUserBlocksAPISerializer(serializers.Serializer):

    #cursor_token max_length is double of usual
    next_or_back = serializers.CharField()
    cursor_token = serializers.CharField(required=False, default='', max_length=200)


    def validate_next_or_back(self, value):

        if value in ['next', 'back']:

            return value

        raise serializers.ValidationError("Accepted values not specified: next/back.")



class UserBannedAudioClipsAPISerializer(serializers.Serializer):

    #cursor_token max_length is double of usual
    next_or_back = serializers.CharField()
    cursor_token = serializers.CharField(required=False, default='', max_length=200)


    def validate_next_or_back(self, value):

        if value in ['next', 'back']:

            return value

        raise serializers.ValidationError("Accepted values not specified: next/back.")

















