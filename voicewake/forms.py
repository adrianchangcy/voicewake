from dataclasses import field
from multiprocessing import Event
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from django.utils import timezone
from pkg_resources import require

from voicewake.models import *

#static values for configuring throughout the app
from .static.values.values import *

#we use forms.py for html form construction and basic validation


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
    
    #use JS to manipulate 'min' date attr
    event_date = forms.DateField(
                    required=False,
                    widget=forms.DateInput(
                                attrs={
                                    'type': 'date',
                                    'required': 'True',
                                    }
                            ),
                    initial=timezone.now().strftime("%Y-%m-%d"),
                )
    
    #make default value be 2 mins ahead, to be received by JS
    global LISTENER_NEW_EVENT_EXTRA_MINUTES
    event_time = forms.TimeField(
                    required=False,
                    widget=forms.TimeInput(
                        attrs={
                            'type': 'time',
                            'required': 'True',
                            'initial_event_time_extra_minutes': LISTENER_NEW_EVENT_EXTRA_MINUTES,
                            }
                        ),
                    label='When',
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
                        'required':'False',
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
                        'required':'False',
                    }
                )
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


class RecordAudioForm(forms.Form):

    audio_file_upload = forms.FileField(
                    label='File to upload',
                    allow_empty_file=False,
                    max_length=50,
                    widget=forms.ClearableFileInput(
                        #until we're sure we can handle more options at server conversion/compression,
                        #only use 3 options
                        attrs={
                            'accept':HTML_FILE_INPUT_ACCEPT,
                        }
                    )
                )

    def clean_audio_file_upload(self):

        file = self.cleaned_data.get('audio_file_upload')

        #validate file size
        if ((file.size) / 1000 ** 2) > MAX_AUDIO_FILE_SIZE_MB:

            raise forms.ValidationError(
                message='Uploaded file size exceeds limit of %(file_size)sMB.',
                params={'file_size' : str(MAX_AUDIO_FILE_SIZE_MB)},
                code='invalid',
            )
        
        #validate file extension (although supposedly useless for security)
        #able to handle '.htaccess', '', 'filename' appropriately
        file_name_extension = (file.name.rsplit('.', 1)[-1]).lower()

        if AUDIO_FILE_EXTENSIONS_ALLOWED.count(file_name_extension) == 0:

            raise forms.ValidationError(
                message='Uploaded file is not supported. Please use: %(file_extensions)s',
                params={'file_extensions' : HTML_FILE_INPUT_ACCEPT},
                code='invalid',
            )

        return file