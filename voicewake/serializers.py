from django.forms import CharField, DateTimeField
from rest_framework import serializers

from .models import *


class AuthUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthUser
        fields = ['username']


class CountriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Countries
        fields = ['id', 'country_name', 'country_name_shortened', 'when_created']


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


class LanguagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Languages
        exclude = ['when_created']


class AuthUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthUser
        fields = ['id', 'username']


class EventLikesDislikesSerializer(serializers.ModelSerializer):
    user = AuthUserSerializer()
    class Meta:
        model = EventLikesDislikes
        fields = '__all__'


class GenericStatusesSerializer(serializers.ModelSerializer):
    class Meta:
        model = GenericStatuses
        exclude = ['when_created', 'last_modified']


class EventRoomsSerializer(serializers.ModelSerializer):
    generic_status = GenericStatusesSerializer()
    locked_for_user = AuthUserSerializer()
    created_by = AuthUserSerializer()
    class Meta:
        model = EventRooms
        fields = '__all__'


class GetEventsSerializer(serializers.ModelSerializer):
    user = AuthUserSerializer()
    event_role = EventRolesSerializer()
    event_tone = EventTonesSerializer()
    event_room = EventRoomsSerializer()
    generic_status = GenericStatusesSerializer()
    audio_file_seconds = serializers.DecimalField(max_digits=6, decimal_places=2, coerce_to_string=False)
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
        fields = ['id', 'user', 'event_role', 'event_tone', 'event_room', 'generic_status', 'audio_file', 'audio_file_seconds', 'audio_volume_peaks', 'like_count', 'dislike_count', 'is_liked_by_user']


class GetEventRoomsSerializer(serializers.Serializer):
    event_room = EventRoomsSerializer()
    originator = GetEventsSerializer()
    responder = serializers.ListField(
        child=GetEventsSerializer()
    )


class CreateEventLikesDislikesSerializer(serializers.Serializer):
    event_id = serializers.IntegerField(required=True)
    is_liked = serializers.BooleanField(required=True, allow_null=True)


class CreateEventsSerializer(serializers.Serializer):

    #pass only when is_originator=False
    event_room_id = serializers.IntegerField(
        required=False,
    )

    #pass only when is_originator=True
    event_room_name = serializers.CharField(
        required=False,
        min_length=1,
        max_length=200, #follow EventRooms.event_room_name
    )

    #BooleanField has bug where if arg is not passed and required=False,
    #it still unintentionally appears in your data with value False
    #https://github.com/encode/django-rest-framework/issues/8300
    is_originator = serializers.BooleanField(
        required=True,
    )
    
    event_tone_id = serializers.IntegerField(
        required=True,
    )

    audio_file = serializers.FileField(
        required=True,
        allow_empty_file=False,
    )

    audio_file_seconds = serializers.DecimalField(
        required=True,
        max_digits=6,
        decimal_places=2,
    )

    audio_volume_peaks = serializers.ListField(
        child=serializers.DecimalField(
            min_value=0,
            max_value=1,
            max_digits=3,
            decimal_places=2
        ),
        min_length=20,
        max_length=20
    )

    def validate(self, data):

        #if originator, must have event_room_name
        #if responder, must have event_tone_id

        if data['is_originator'] is True and 'event_room_name' in data:

            return data
        
        elif data['is_originator'] is False and 'event_room_id' in data:

            return data
        
        else:

            raise serializers.ValidationError('Missing paired data on is_originator.')


class UserActionsSerializer(serializers.Serializer):
    event_room_id = serializers.IntegerField()
    to_reply = serializers.BooleanField(allow_null=True, default=None)

    def validate(self, data):

        if 'event_room_id' in data and 'to_reply' in data:

            return data
        
        else:

            raise serializers.ValidationError('Missing paired data.')


