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
from rest_framework import viewsets, generics
    #ModelViewSet has: list, create, retrieve, update, partial_update, destroy
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.views.generic.edit import FormView
from django.views.generic.list import ListView
from django.views.generic import TemplateView

#mixins
from django.contrib.auth.mixins import PermissionRequiredMixin

#Python libraries
from datetime import datetime, timezone, timedelta
import zoneinfo
import os
import json

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
class UserVerificationOptionsAPI(PermissionPolicyMixin, viewsets.ModelViewSet):

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



#=====REST APIs=====

class EventTonesAPI(viewsets.ReadOnlyModelViewSet):

    serializer_class = EventTonesSerializer
    queryset = EventTones.objects.all()

    def get_queryset(self):

        search = self.request.query_params.get('search')

        if search is not None:

            #part of search optimisation is "... field_name LIKE 'string%' OR field_name LIKE '%string%'"
            #Q is used to encapsulate a collection of keyword arguments
            return EventTones.objects.filter(
                        Q(event_tone_name__istartswith=search)|Q(event_tone_name__icontains=search)
                        )[:10]
            
        else:
        
            return EventTones.objects.all()


class LanguagesAPI(viewsets.ModelViewSet):

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


#we get events via event_room, as they all must belong to a room
class EventsAPI(generics.ListAPIView):

    def get_queryset(self, **kwargs):
        
        if 'event_room_id' in kwargs:

            return Events.objects.filter(event_room=EventRooms(pk=kwargs['event_room_id']))
        
        else:

            return []
        
    def get(self, request, *args, **kwargs):

        serializer = EventsSerializer(self.get_queryset(**kwargs), many=True)

        return Response(serializer.data)


#=====END OF REST APIs=====


#=====WEB PAGES=====

#create main events
class CreateMainEvents(FormView):

    template_name = 'voicewake/events/create_main_events.html'
    form_class = CreateMainEventsForm
    success_url = '/'

    def form_valid(self, form):

        user_event_role = UserEventRoles.objects.get(
            user=AuthUser(pk = getattr(self.request.user, 'id')),
            event_role__event_role_name='originator'
        )

        try:

            event_tone = EventTones.objects.get(id=form.cleaned_data['event_tone_id'])

        except EventTones.DoesNotExist:

            return JsonResponse({'message':'Invalid event_tone_id.'}, status=status.HTTP_400_BAD_REQUEST)

        #create event, excluding audio_file and event_room_id
        new_event = Events.objects.create(
            user_event_role=user_event_role,
            event_name=form.cleaned_data['event_name'],
            event_tone=event_tone,
            event_status=EventStatuses.objects.filter(event_status_name='available')[:1].get(),
        )

        #create event_room_id
        new_event.event_room = EventRooms.objects.create()

        #save audio_file here to allow reference to model instance, as it now exists
        new_event.audio_file = form.cleaned_data['audio_file']

        new_event.save()

        #don't return super().form_valid(form), else it goes though form.save() again
        return JsonResponse(data={}, status=status.HTTP_201_CREATED)


#view specific event
#to fetch replies and create new reply, we use EventsByRoom viewset
class ViewSpecificEvents(FormView):

    template_name = 'voicewake/events/view_specific_events.html'

    def get(self, request, *args, **kwargs):

        #originator event
        #should always have only 1 per room
        try:

            originator_event = Events.objects.get(
                event_room=EventRooms(pk=kwargs['event_room_id']),
                user_event_role__event_role__event_role_name='originator'
            )

        except Events.DoesNotExist:

            return JsonResponse({'message':'Originator event does not exist.'}, status=status.HTTP_404_NOT_FOUND)

        return render(
            request,
            template_name='voicewake/events/view_specific_events.html',
            context={
            'originator_event': originator_event,
            }
        )


#browse main events, i.e. view list before selecting a specific one
class BrowseMainEvents(ListView):

    template_name = 'voicewake/events/browse_main_events.html'

    def get_queryset(self):

        events = [1,1]

        return events



#=====END OF WEB PAGES=====
