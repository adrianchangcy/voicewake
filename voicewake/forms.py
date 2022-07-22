from dataclasses import field
from multiprocessing import Event
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from django.utils import timezone

from voicewake.models import *


#we use forms.py for html form construction and basic validation
#you will have to use JS for auto-complete dropdown on these CharFields



class UserSignUpForm(UserCreationForm):

    email = forms.EmailField(required=True)
        #line above is purely to tell middleware or backend processes about the args
        #i.e. "hey, this field will be required"

    class Meta:
        app_label = 'voicewake'
        model = User
        fields = ['username', 'email', 'password1', 'password2']



class CreateEventsForm(forms.Form):

    event_name = forms.CharField(
                    required=False,
                    widget=forms.TextInput(
                                attrs={
                                    'required': 'True'
                                }
                            ),
                )
    
    event_date_minimum_value = timezone.now().strftime("%Y-%m-%d")
    event_date = forms.DateField(
                    required=False,
                    widget=forms.DateInput(
                                attrs={
                                    'type': 'date',
                                    'required': 'True',
                                    'min': event_date_minimum_value,
                                    }
                            ),
                    initial=timezone.now().strftime("%Y-%m-%d"),
                )
    
    #do 10 min headstart
    event_time_initial_value = (timezone.now() + timedelta(minutes=10)).strftime("%H:%M")
    event_time = forms.TimeField(
                    required=False,
                    widget=forms.TimeInput(
                        attrs={
                            'type': 'time',
                            'required': 'True',
                            }
                        ),
                    initial=event_time_initial_value,
                    label='this is how you customise label content'
                )

    #we do radios like this, else "enter a list of values" error
    #many-to-many field handler is expecting [] or [valid str IDs to convert to actual model instance], but is getting only str
    class ModelCommaSeparatedChoiceField(forms.ModelMultipleChoiceField):
        widget = forms.RadioSelect(
                    attrs={
                        'required': 'True'
                    }
                )
        def clean(self, value):
            if value is not None:
                value = [item.strip() for item in value.split(',')] #remove padding, encase in []
            return super().clean(value)

    event_purpose = ModelCommaSeparatedChoiceField(
                        required=False,
                        queryset=EventPurposes.objects.all(),
                        
                    )

    event_tone = ModelCommaSeparatedChoiceField(
                    required=False,
                    queryset=EventTones.objects.all(),
    )

    language = ModelCommaSeparatedChoiceField(
                        required=False,
                        queryset=Languages.objects.all(),
                    )

    event_message = forms.CharField(required=False)



class SeekEventsForm(forms.Form):

    EVENT_MODE_CHOICES = [(1, 'live'), (2, 'pre-record'), (3, 'any')]

    event_mode_choice = forms.ChoiceField(
                    label='Mode',
                    required=False,
                    choices=EVENT_MODE_CHOICES,
                    initial=3,
                    widget=forms.Select(
                        attrs={
                            'required':'True',
                        }
                    )
                )

    EVENT_SCOPE_CHOICES = [(1,'individual'), (2,'group'), (3,'any')]

    event_scope_choice = forms.ChoiceField(
                    label='Scope',
                    required=False,
                    choices=EVENT_SCOPE_CHOICES,
                    initial=3,
                    widget=forms.Select(
                        attrs={
                            'required':'True',
                        }
                    )
                )
    
    language = forms.CharField(
                label='Language',
                required=False,
                widget=forms.TextInput(
                    attrs={
                        'class':'reuse_basic_autocomplete',
                        'table_name':'languages',
                        'column_name':'language_name',
                        'placeholder':'Your spoken language',
                        'required':'True',
                    }
                )
            )

    event_purpose = forms.CharField(
                label='Purpose',
                required=False,
                widget=forms.TextInput(
                    attrs={
                        'class':'reuse_basic_autocomplete',
                        'table_name':'event_purposes',
                        'column_name':'event_purpose_name',
                        'placeholder':'Purpose',
                        'required':'True',
                    }
                )
            )

    event_tone = forms.CharField(
                label='Tone',
                required=False,
                widget=forms.TextInput(
                    attrs={
                        'class':'reuse_basic_autocomplete',
                        'table_name':'event_tones',
                        'column_name':'event_tone_name',
                        'placeholder':'Tone',
                        'required':'True',
                    }
                )
            )