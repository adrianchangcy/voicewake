from dataclasses import field
from multiprocessing import Event
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from django.utils import timezone

from voicewake.models import UserDetails, EventPurposes, Languages


#use forms.py only for validation


class UserSignUpForm(UserCreationForm):

    email = forms.EmailField(required=True)
        #line above is purely to tell middleware or backend processes about the args
        #i.e. "hey, this field will be required"

    class Meta:
        app_label = 'voicewake'
        model = User
        fields = ['username', 'email', 'password1', 'password2']



class CreateEventForm(forms.Form):

    #HOW TO AUTO-GENERATE FORM
    #FormView passes 'form' to template
    #so to auto-generate form fields from here, call form.as_p at template

    #HOW TO SPECIFY INPUT TYPE IN DJANGO'S forms AT forms.py
    # from django import forms
    #e.g.:
    # event_date = forms.DateField(
    #                 widget=forms.DateInput(attrs={'type': 'date'}),
    #                 initial=datetime.now().strftime("%Y-%m-%d")
    #             )

    #HOW TO INITIALISE DJANGO'S FORM FIELD WITH QUERYSET DATA
    #for static data, use forms.MultipleChoiceField(choices=[])
    #for dynamic data, i.e. queryset, use forms.ModelMultipleChoiceField(queryset=...)
        #with this method, if you do not override __str__ in your model class at models.py,
        #the data displayed at form will be "ClassName object (1)"
            #override it like so to make a column the default string value for 'queryset' arg:
                # class ModelClassName(models.Model):
                #     #...
                #     def __str__(self):
                #         return self.column_name

    #PYTHON
    #DIFFERENCE BETWEEN __str__ AND __repr__
    #__str__ is intended to return a user-friendly description of an object
    #__repr__ is intended to return a developer-friendly string description of an object
    #they are Python's built-in special methods of an object that produces textual representation
        #on object usage, you can manually get them via str(objectvar) and repr(objectvar),
        #or objectvar.__str__() and objectvar.__repr__()
    #you can specify what an object returns when these are called, by implementing them:
        # class ClassName:
        #     def __init__(self, name):
        #         self.name = name
        #     def __str__(self):
        #         return f'I am {self.name}'
        #     def __repr__(self):
        #         return f'ClassName("{self.name}")'
    
    #real-life usage, e.g.:
    # from datetime import datetime
    # today = datetime.now()
    # print(str(today))   #2021-10-14 10:15:31.405463
    # print(repr(today))  #datetime.datetime(2021, 10, 14, 10, 15, 31, 405463)

    #DJANGO TEMPLATES
    #UNPACKING DICT IN TEMPLATES
    #e.g. {'keyname0':0, 'keyname1':1}
    #much like how .items() is crucial for unpacking dict into tuples for python,
    #just put .items in templates, e.g.:
        #{%for key, val in passed_dict_var.items%}
        #...
        #{%endfor}


    #preparing data

    event_purposes_list = EventPurposes.objects.all()
    
    # languages_list = list(Languages.objects.all())
    # languages_list.append(('language_name','Any'))  #does it work?
    
    #form attributes
    #some will have required=False to remove '... required' message
    #but behaviour is still True via attrs{'required':'True'}

    event_name = forms.CharField(
                    required=False,
                    widget=forms.TextInput(
                                attrs={
                                    'required': 'True'
                                }
                            ),
                )
    
    event_date = forms.DateField(
                    required=False,
                    widget=forms.DateInput(
                                attrs={
                                    'type': 'date',
                                    'required': 'True'
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
                            'required': 'True'
                            }
                        ),
                    initial=event_time_initial_value
                )

    event_purpose = forms.ModelMultipleChoiceField(
                        required=False,
                        widget=forms.RadioSelect(
                                    attrs={
                                        'required': 'True'
                                    }
                            ),
                        queryset=EventPurposes.objects.all(),
                    )

    event_tone = forms.CharField(required=False)
    
    # #v1?
    # event_language = forms.CharField(
    #                     required=True,
    #                     label="pick language boi",
    #                     widget=forms.Select(choices=languages_list),
    #                 )
    # #v2?
    # event_language = forms.ChoiceField(
    #                     required=True,
    #                     label="pick language boi",
    #                     widget=forms.Select,
    #                     choices=languages_list
    #                 )

    event_message = forms.CharField(required=False)

    print(event_time)