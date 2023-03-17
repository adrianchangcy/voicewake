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


class UserEventRolesSerializer(serializers.ModelSerializer):
    user = AuthUserSerializer()
    class Meta:
        model = UserEventRoles
        fields = '__all__'


class EventsSerializer(serializers.ModelSerializer):
    user_event_role = UserEventRolesSerializer()
    class Meta:
        model = Events
        fields = '__all__'





