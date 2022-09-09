from django import views
from django.http import JsonResponse, QueryDict
from django.db.models import Q
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, permission_required
from django.db import connection

from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.authtoken.models import Token

#class-based views
from rest_framework import viewsets
    #ModelViewSet has: list, create, retrieve, update, partial_update, destroy
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.views.generic.edit import FormView
from django.views.generic.list import ListView

#mixins
from django.contrib.auth.mixins import PermissionRequiredMixin

#Python libraries
from datetime import datetime, timezone, timedelta
import zoneinfo
import os

#app files
from voicewake.forms import *
from .models import *
from .serializers import *
from .services import *

#static values for configuring throughout the app
from .static.values.values import *


#overriding ModelViewSet's check_permissions() via super() to allow permission_classes_per_method
class PermissionPolicyMixin():
    
    def check_permissions(self, request):
        try:
            # This line is heavily inspired from `APIView.dispatch`.
            # It returns the method associated with an endpoint.
            handler = getattr(self, request.method.lower())
        except AttributeError:
            handler = None

        if (
            handler
            and self.permission_classes_per_method
            and self.permission_classes_per_method.get(handler.__name__)
        ):
            self.permission_classes = self.permission_classes_per_method.get(handler.__name__)

        super().check_permissions(request)


# #TESTING AREA
# @api_view(['GET','POST'])
# # @permission_required('voicewake.can_fart', login_url='/login', raise_exception=True)
# def user_verification_options_list(request, format=None):

#     #TESTING AREA
#     #======================


#     # if request.user.is_superuser:

#     #     print('hooray')

#     # boom = UserVerificationOptions.objects.exclude(pk=1, user_verification_option_name="Instagram")

#     # if boom:

#     #     print('waddup')

#     # serializer = UserVerificationOptionsSerializer(boom, many=True)

#     # return JsonResponse(data={'user_verification_options':serializer.data}, status=status.HTTP_418_IM_A_TEAPOT)
#     # return
#     #======================

#     if request.method == 'GET':

#         user_verification_options = UserVerificationOptions.objects.all()
#         serializer = UserVerificationOptionsSerializer(user_verification_options, many=True)

#         return Response(serializer.data)

#     elif request.method == 'POST':

#         serializer = UserVerificationOptionsSerializer(data=request.data)

#         if serializer.is_valid():

#             serializer.save()
#             return JsonResponse(data={'user_verification_options':serializer.data}, status=status.HTTP_201_CREATED)

#     return JsonResponse(data={'detail':'invalid request type'}, status=status.HTTP_418_IM_A_TEAPOT)


# @api_view(['GET', 'PUT', 'DELETE'])
# def user_verification_options_details(request, id, format=None):

#     try:

#         user_verification_option = UserVerificationOptions.objects.get(pk=id)

#     except UserVerificationOptions.DoesNotExist:
        
#         return Response(status=status.HTTP_404_NOT_FOUND)

#     if request.method == 'GET':

#         serializer = UserVerificationOptionsSerializer(user_verification_option)

#         return JsonResponse({"user_verification_options":serializer.data}, safe=False)

#     elif request.method == 'PUT':

#         #request.data is just plain dict of passed data
#         #so you can manually modify it as such, e.g. request.data.update({})

#         serializer = UserVerificationOptionsSerializer(user_verification_option, data=request.data)

#         if serializer.is_valid():

#             serializer.save()
#             #you can also pass data changes into .save() in kwargs fashion:
#             # serializer.save(user_verification_option_name="clown")

#             return JsonResponse({"user_verification_option":serializer.data}, safe=False)

#     elif request.method == 'DELETE':

#         user_verification_option.delete()

#         return Response(status=status.HTTP_204_NO_CONTENT)

#     return Response(status=status.HTTP_418_IM_A_TEAPOT)



# @login_required(login_url='/login')
def home(request):

    return render(request, template_name='voicewake/home.html')


def sign_up(request):

    if request.method == 'POST':

        form = UserSignUpForm(request.POST)

        if form.is_valid():

            user = form.save()

            Token.objects.create(user=user)

            login(request, user)
            return redirect('/')

    else:

        #show empty form
        form = UserSignUpForm()

    return render(request, 'registration/sign_up.html', {"form":form})


#TBD
#TEST SETTING TIME ZONE
common_timezones = {
    'London': 'Europe/London',
    'Paris': 'Europe/Paris',
    'New York': 'America/New_York',
}
def set_timezone(request):

    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect('/')
    else:
        return render(request, 'voicewake/set_timezone.html', {'timezones': common_timezones})









# class UserVerificationOptionsViewSet(PermissionRequiredMixin, viewsets.ModelViewSet):
class UserVerificationOptionsViewSet(PermissionPolicyMixin, viewsets.ModelViewSet):

    # authentication_classes = [SessionAuthentication, BasicAuthentication]
    # permission_classes = [IsAuthenticated]

    #leave empty or specify ('app_name.permission_code_name1', 'app_name.permission_code_name2')
    # permission_required = ()

    permission_classes_per_method = {
        'list' : [IsAdminUser]
    }

    serializer_class = UserVerificationOptionsSerializer
    queryset = UserVerificationOptions.objects.all()


            
    #if you have a function here, you can override viewset-level configs for the function, e.g.:
    # from rest_framework.decorators import action
    # @action(detail=True, methods=['post'], permission_classes=[IsAdminOrIsSelf])



#PROGESS STARTS HERE

#=====REST APIs=====

class EventPurposesViewSet(viewsets.ModelViewSet):

    serializer_class = EventPurposesSerializer
    permission_classes = [IsAuthenticated]
    queryset = EventPurposes.objects.all()

    def get_queryset(self):

        #allow max 50 rows
        queryset = EventPurposes.objects.all()[:50]

        search = self.request.query_params.get('search')

        if search is not None:

            #part of search optimisation is "... field_name LIKE 'string%' OR field_name LIKE '%string%'"
            #Q is used to encapsulate a collection of keyword arguments
            queryset = EventPurposes.objects.filter(
                        Q(event_purpose_name__istartswith=search)|Q(event_purpose_name__icontains=search)
                        )[:10]

        return queryset


class EventTonesViewSet(viewsets.ModelViewSet):

    serializer_class = EventTonesSerializer
    permission_classes = [IsAuthenticated]
    queryset = EventTones.objects.all()

    def get_queryset(self):

        #allow max 50 rows
        queryset = EventTones.objects.all()[:50]

        search = self.request.query_params.get('search')

        if search is not None:

            #part of search optimisation is "... field_name LIKE 'string%' OR field_name LIKE '%string%'"
            #Q is used to encapsulate a collection of keyword arguments
            queryset = EventTones.objects.filter(
                        Q(event_tone_name__istartswith=search)|Q(event_tone_name__icontains=search)
                        )[:10]

        return queryset


class LanguagesViewSet(viewsets.ModelViewSet):

    serializer_class = LanguagesSerializer
    permission_classes = [IsAuthenticated]
    queryset = Languages.objects.all()

    def get_queryset(self):

        #allow max 50 rows
        queryset = Languages.objects.all()[:50]

        search = self.request.query_params.get('search')

        if search is not None:

            #part of search optimisation is "... field_name LIKE 'string%' OR field_name LIKE '%string%'"
            #Q is used to encapsulate a collection of keyword arguments
            queryset = Languages.objects.filter(
                        Q(language_name__istartswith=search)|Q(language_name__icontains=search)
                        )[:10]

        return queryset



#=====END OF REST APIs=====


#=====WEB PAGES=====

#create listener event
class CreateEventsFormView(FormView):

    template_name = 'voicewake/events/listeners/create_events.html'
    form_class = CreateEventsForm
    success_url = '/'

    def form_valid(self, form):

        #by inheriting ProcessFormView, during post(), it already checks for is_valid()
            #clean() is part of the validation in is_valid()
        #when is_valid() is True, it then calls form_valid(), else form_invalid()
        #this applies to CreateView, FormView, UpdateView

        user_event_role = UserEventRoles.objects.get(
            user=self.request.user.id,
            event_role__event_role_name='listener'
        )

        #for USE_TZ=True, use tzinfo attr for timezone-aware, else warning
        #make sure JS processes form datetime into UTC before this
        event_datetime = datetime.combine(
                            form.cleaned_data['event_date'],
                            form.cleaned_data['event_time'],
                            tzinfo=zoneinfo.ZoneInfo('UTC'))

        new_event = Events.objects.create(
            user_event_role=user_event_role,
            event_name=form.cleaned_data['event_name'],
            event_purpose=EventPurposes.objects.get_or_create(event_purpose_name=form.cleaned_data['event_purpose'])[0],
            event_tone=EventTones.objects.get_or_create(event_tone_name=form.cleaned_data['event_tone'])[0],
            language=Languages.objects.get_or_create(language_name=form.cleaned_data['language'])[0],
            event_message=form.cleaned_data['event_message'],
            event_status=EventStatuses.objects.filter(event_status_name='available')[:1].get(),
            when_trigger=event_datetime,
        )

        #form currently does not handle EventRepeatDetails
        #only create new EventRepeatDetails obj in db if one of those columns are specified

        #to-do: please clarify that timezone adjustments are accurate

        #don't return super().form_valid(form), else it goes though form.save() again
        return redirect('/create-event')


#view personal events
class ViewEventsListView(ListView):

    template_name = 'voicewake/events/listeners/view_events.html'

    def get_queryset(self):

        user_event_role = UserEventRoles.objects.get(
                                                    user=self.request.user.id,
                                                    event_role__event_role_name='listener'
                                                    )

        # queryset = EventSchedules.objects.select_ related('event').filter(event__user_event_role=user_event_role)
        events = Events.objects.filter(user_event_role=user_event_role)

        return events

#find match
class SeekEventsFormView(FormView):

    template_name = 'voicewake/events/talkers/seek_events.html'
    form_class = SeekEventsForm
    success_url = '/'

    def form_valid(self, form):

        global QUALIFY_FOR_LIVE_TIME_WINDOW


        return redirect('/seek-event')

        user_event_role = UserEventRoles.objects.get(
                                                    user=self.request.user.id,
                                                    event_role__event_role_name='talker'
                                                    )

        #search for listeners to match first
        #the rest of the code can be skipped if no rows found
        event_mode_choice = form.cleaned_data['event_mode_choice']
        event_scope_choice = form.cleaned_data['event_scope_choice']

        #on live 1-1 search (not doing 1-many for live)
        """
        SELECT id FROM events WHERE 
            event_status_id=(SELECT id FROM event_statuses WHERE event_status_name='available')
            AND when_trigger < yourdatetime_after_60_secs_from_now
        LIMIT 1;

        INSERT INTO event_rooms DEFAULT VALUES;

        """

        #on group search
        """
        
        """


        #create event
        #not specifying when_trigger here to use auto_add_now=True
        # new_event = Events.objects.create(
        #     user_event_role=user_event_role,
        #     event_purpose=EventPurposes.objects.get_or_create(event_purpose_name=form.cleaned_data['event_purpose']),
        #     event_tone=EventTones.objects.get_or_create(event_tone_name=form.cleaned_data['event_tone']),
        #     language=Languages.objects.get_or_create(language_name=form.cleaned_data['language']),
        #     event_status=EventStatuses.objects.filter(event_status_name='available').first(),
        # )

        return redirect('/seek-event')

#test record
class RecordAudioFormView(FormView):

    template_name = 'voicewake/events/talkers/record_audio.html'
    form_class = RecordAudioForm
    success_url = '/record'
    
    def form_valid(self, form):

        return redirect('/record')
        #when you want to open the file, use chunks in loop instead of read()
        #https://docs.djangoproject.com/en/4.1/ref/files/uploads/
        # convert_audio_files_to_mp3()

        #maybe run codes from services.py, i.e. our self-made middle layer for business logic
        #check these two links for looping on query rows
            #https://stackoverflow.com/questions/6069024/syntax-of-for-loop-in-sql-server
            #https://stackoverflow.com/questions/32668201/postgresql-iterate-over-results-of-query
        #for more docs on consumer for websocket
            #https://channels.readthedocs.io/en/latest/topics/consumers.html


#=====END OF WEB PAGES=====
