from django import views
from django.http import JsonResponse, QueryDict
from django.db.models import Case, Value, When, Sum, Q
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


#if empty db, run this
def first_time_setup():

    from django.contrib.auth.models import Group

    if EventTones.objects.count() == 0:

        EventTones.objects.bulk_create([
            EventTones(event_tone_name='blank face', event_tone_symbol='😶'),
            EventTones(event_tone_name='plain smile', event_tone_symbol='🙂'),
            EventTones(event_tone_name='smile', event_tone_symbol='😄'),
            EventTones(event_tone_name='smiley', event_tone_symbol='😃'),
            EventTones(event_tone_name='grinning', event_tone_symbol='😀'),
            EventTones(event_tone_name='blush', event_tone_symbol='😊'),
            EventTones(event_tone_name='halo', event_tone_symbol='😇'),
            EventTones(event_tone_name='wink', event_tone_symbol='😉'),
            EventTones(event_tone_name='heart eyes', event_tone_symbol='😍'),
            EventTones(event_tone_name='kissing heart', event_tone_symbol='😘'),
            EventTones(event_tone_name='kissing flushed', event_tone_symbol='😚'),
            EventTones(event_tone_name='kissing', event_tone_symbol='😗'),
            EventTones(event_tone_name='kissing smiling eyes', event_tone_symbol='😙'),
            EventTones(event_tone_name='stuck out tongue winking eye', event_tone_symbol='😜'),
            EventTones(event_tone_name='stuck out tongue closed eyes', event_tone_symbol='😝'),
            EventTones(event_tone_name='stuck out tongue', event_tone_symbol='😛'),
            EventTones(event_tone_name='flushed', event_tone_symbol='😳'),
            EventTones(event_tone_name='grin', event_tone_symbol='😁'),
            EventTones(event_tone_name='pensive', event_tone_symbol='😔'),
            EventTones(event_tone_name='relieved', event_tone_symbol='😌'),
            EventTones(event_tone_name='unamused', event_tone_symbol='😒'),
            EventTones(event_tone_name='disappointed', event_tone_symbol='😞'),
            EventTones(event_tone_name='persevere', event_tone_symbol='😣'),
            EventTones(event_tone_name='cry', event_tone_symbol='😢'),
            EventTones(event_tone_name='joy', event_tone_symbol='😂'),
            EventTones(event_tone_name='sob', event_tone_symbol='😭'),
            EventTones(event_tone_name='sleepy', event_tone_symbol='😪'),
            EventTones(event_tone_name='disappointed relieved', event_tone_symbol='😥'),
            EventTones(event_tone_name='cold sweat', event_tone_symbol='😰'),
            EventTones(event_tone_name='sweat smile', event_tone_symbol='😅'),
            EventTones(event_tone_name='sweat', event_tone_symbol='😓'),
            EventTones(event_tone_name='weary', event_tone_symbol='😩'),
            EventTones(event_tone_name='tired face', event_tone_symbol='😫'),
            EventTones(event_tone_name='fearful', event_tone_symbol='😨'),
            EventTones(event_tone_name='scream', event_tone_symbol='😱'),
            EventTones(event_tone_name='angry', event_tone_symbol='😠'),
            EventTones(event_tone_name='rage', event_tone_symbol='😡'),
            EventTones(event_tone_name='triumph', event_tone_symbol='😤'),
            EventTones(event_tone_name='confounded', event_tone_symbol='😖'),
            EventTones(event_tone_name='laughing', event_tone_symbol='😆'),
            EventTones(event_tone_name='yum', event_tone_symbol='😋'),
            EventTones(event_tone_name='injured', event_tone_symbol='🤕'),
            EventTones(event_tone_name='mask', event_tone_symbol='😷'),
            EventTones(event_tone_name='fever', event_tone_symbol='🤒'),
            EventTones(event_tone_name='nauseating', event_tone_symbol='🤢'),
            EventTones(event_tone_name='heated', event_tone_symbol='🥵'),
            EventTones(event_tone_name='chilled', event_tone_symbol='🥶'),
            EventTones(event_tone_name='sunglasses', event_tone_symbol='😎'),
            EventTones(event_tone_name='cowboy', event_tone_symbol='🤠'),
            EventTones(event_tone_name='money face', event_tone_symbol='🤑'),
            EventTones(event_tone_name='party face', event_tone_symbol='🥳'),
            EventTones(event_tone_name='sleeping', event_tone_symbol='😴'),
            EventTones(event_tone_name='dizzy face', event_tone_symbol='😵'),
            EventTones(event_tone_name='astonished', event_tone_symbol='😲'),
            EventTones(event_tone_name='worried', event_tone_symbol='😟'),
            EventTones(event_tone_name='frowning', event_tone_symbol='😦'),
            EventTones(event_tone_name='anguished', event_tone_symbol='😧'),
            EventTones(event_tone_name='imp', event_tone_symbol='👿'),
            EventTones(event_tone_name='open mouth', event_tone_symbol='😮'),
            EventTones(event_tone_name='grimacing', event_tone_symbol='😬'),
            EventTones(event_tone_name='neutral face', event_tone_symbol='😐'),
            EventTones(event_tone_name='confused', event_tone_symbol='😕'),
            EventTones(event_tone_name='hushed', event_tone_symbol='😯'),
            EventTones(event_tone_name='smirk', event_tone_symbol='😏'),
            EventTones(event_tone_name='expressionless', event_tone_symbol='😑'),
            EventTones(event_tone_name='baby', event_tone_symbol='👶'),
            EventTones(event_tone_name='older man', event_tone_symbol='👴'),
            EventTones(event_tone_name='older woman', event_tone_symbol='👵'),
            EventTones(event_tone_name='angel', event_tone_symbol='👼'),
            EventTones(event_tone_name='princess', event_tone_symbol='👸'),
            EventTones(event_tone_name='see no evil', event_tone_symbol='🙈'),
            EventTones(event_tone_name='hear no evil', event_tone_symbol='🙉'),
            EventTones(event_tone_name='speak no evil', event_tone_symbol='🙊'),
            EventTones(event_tone_name='clown', event_tone_symbol='🤡'),
            EventTones(event_tone_name='moyai', event_tone_symbol='🗿'),
            EventTones(event_tone_name='skull', event_tone_symbol='💀'),
            EventTones(event_tone_name='alien', event_tone_symbol='👽'),
            EventTones(event_tone_name='hankey', event_tone_symbol='💩'),
            EventTones(event_tone_name='wave', event_tone_symbol='👋'),
            EventTones(event_tone_name='pray', event_tone_symbol='🙏'),
            EventTones(event_tone_name='clap', event_tone_symbol='👏'),
            EventTones(event_tone_name='muscle', event_tone_symbol='💪'),
            EventTones(event_tone_name='bow', event_tone_symbol='🙇'),
            EventTones(event_tone_name='broken heart', event_tone_symbol='💔'),
            EventTones(event_tone_name='two hearts', event_tone_symbol='💕'),
            EventTones(event_tone_name='sparkling heart', event_tone_symbol='💖'),
            EventTones(event_tone_name='revolving hearts', event_tone_symbol='💞'),
            EventTones(event_tone_name='cupid', event_tone_symbol='💘'),
            EventTones(event_tone_name='turtle', event_tone_symbol='🐢'),
            EventTones(event_tone_name='snail', event_tone_symbol='🐌'),
            EventTones(event_tone_name='octopus', event_tone_symbol='🐙'),
            EventTones(event_tone_name='four leaf clover', event_tone_symbol='🍀'),
            EventTones(event_tone_name='herb', event_tone_symbol='🌿'),
            EventTones(event_tone_name='hourglass flowing sand', event_tone_symbol='⏳'),
            EventTones(event_tone_name='hourglass', event_tone_symbol='⌛'),
            EventTones(event_tone_name='game die', event_tone_symbol='🎲'),
            EventTones(event_tone_name='checkered flag', event_tone_symbol='🏁'),
            EventTones(event_tone_name='trophy', event_tone_symbol='🏆'),
            EventTones(event_tone_name='roller coaster', event_tone_symbol='🎢'),
            EventTones(event_tone_name='rocket', event_tone_symbol='🚀'),
            EventTones(event_tone_name='keep it 100', event_tone_symbol='💯'),
        ])

    if Countries.objects.count() == 0:

        Countries.objects.create(
            country_name='United States of America',
            country_name_shortened='USA'
        )

    if Languages.objects.count() == 0:

        Languages.objects.create(
                    language_name='English',
                    language_name_shortened='ENG'
        )

    if Group.objects.count() == 0:

        Group.objects.create(
            name='regular'
        )

    if EventRoles.objects.count() == 0:

        EventRoles.objects.bulk_create([
            EventRoles(event_role_name='originator'),
            EventRoles(event_role_name='responder')
        ])


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
class EventsAPI(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = GetEventsSerializer
    queryset = None

    def get_queryset(self):

        if 'event_room_id' in self.kwargs:

            event_room_id = self.kwargs['event_room_id']

        else:

            return []        

        events = Events.objects.filter(
            event_room=EventRooms(pk=event_room_id)
        ).annotate(
            like_count=Sum(
                Case(
                    When(eventlikesdislikes__is_liked=True, then=Value(1)),
                    default=0
                )
            )
        ).annotate(
            dislike_count=Sum(
                Case(
                    When(eventlikesdislikes__is_liked=False, then=Value(1)),
                    default=0
                )
            )
        ).annotate(
            is_liked_by_user=Case(
                When(
                    eventlikesdislikes__user=AuthUser(pk=self.request.user.id),
                    eventlikesdislikes__is_liked=True,
                    then=Value(True)
                ),
                When(
                    eventlikesdislikes__user=AuthUser(pk=self.request.user.id),
                    eventlikesdislikes__is_liked=False,
                    then=Value(False)
                ),
                default=Value(None)
            )
        ).order_by('when_created')

        #you can return events.values() and skip GetEventsSerializer, but idk about the pros and cons
        return events

    def get(self, request, *args, **kwargs):

        return Response(GetEventsSerializer(self.get_queryset(), many=True).data)
    
    def post(self, request, *args, **kwargs):
        
        serializer = CreateEventsSerializer(data=request.data, many=False)

        if serializer.is_valid() is False:

            return Response(data={}, status=status.HTTP_400_BAD_REQUEST)
        
        new_data = serializer.validated_data

        if new_data['is_originator'] is True:

            #originator
            user_event_role = UserEventRoles.objects.get(
                user=AuthUser(pk = getattr(self.request.user, 'id')),
                event_role__event_role_name='originator'
            )

        else:
            
            #responder
            user_event_role = UserEventRoles.objects.get(
                user=AuthUser(pk = getattr(self.request.user, 'id')),
                event_role__event_role_name='responder'
            )

        #create event, excluding audio_file and event_room_id
        new_event = Events.objects.create(
            user_event_role=user_event_role,
            event_tone=EventTones(pk=new_data['event_tone_id']),
            audio_volume_peaks = new_data['audio_volume_peaks'],
        )

        if new_data['is_originator'] is True:

            #create event_room row if user is originator
            new_event.event_room = EventRooms.objects.create(
                event_room_name=new_data['event_room_name'],
            )

        else:

            #get specified event_room if user is responder
            new_event.event_room = EventRooms(pk=new_data['event_room_id'])

        #we delay saving audio_file, as we want when_created first
        new_event.audio_file = new_data['audio_file']

        new_event.save()

        #don't return super().form_valid(form), else it goes though form.save() again
        return JsonResponse(data={}, status=status.HTTP_201_CREATED)







#to submit likes/dislikes
#is_liked=True/False, or destroy when undone
class EventLikesDislikesAPI(generics.GenericAPIView):

    serializer_class = EventLikesDislikesSerializer

    #create
    def put(self, request, *args, **kwargs):

        if 'event_id' not in request.data or 'is_liked' not in request.data:

            return Response(status=status.HTTP_400_BAD_REQUEST)
        
        event_id = json.loads(request.data['event_id'])
        is_liked = json.loads(request.data['is_liked'])

        if type(event_id) != int or type(is_liked) != bool:

            return Response(status=status.HTTP_400_BAD_REQUEST)

        #create or update
        try:

            instance = EventLikesDislikes.objects.get(
                event=Events(pk=event_id),
                user=AuthUser(pk=request.user.id)
            )

            instance.is_liked = is_liked
            instance.save()

        except EventLikesDislikes.DoesNotExist:

            instance = EventLikesDislikes.objects.create(
                event=Events(pk=event_id),
                user=AuthUser(pk=request.user.id),
                is_liked=is_liked
            )

        return Response(status=status.HTTP_200_OK)
    

    #we use POST instead of DELETE because DELETE does not have request.data
    #more convenient than creating another URL for this
    def post(self, request, *args, **kwargs):

        if 'event_id' not in request.data:

            return Response(status=status.HTTP_400_BAD_REQUEST)

        event_id = json.loads(request.data['event_id'])

        if type(event_id) != int:

            return Response(status=status.HTTP_400_BAD_REQUEST)

        #get first
        try:

            instance = EventLikesDislikes.objects.get(
                event=Events(pk=event_id),
                user=AuthUser(pk=request.user.id)
            )
        
        except EventLikesDislikes.DoesNotExist:

            return Response(status=status.HTTP_204_NO_CONTENT)

        #delete
        instance.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


#=====END OF REST APIs=====


#=====WEB PAGES=====

#create main events
#handles originator events
class CreateMainEvents(FormView):

    template_name = 'voicewake/events/create_main_events.html'
    form_class = CreateMainEventsForm
    success_url = '/'

    #this is originally originator + responder handler, but responder is currently separated
    def form_valid(self, form):

        #ensure we have the right set of data needed
        if form.cleaned_data['is_originator'] is True:

            #originator
            user_event_role = UserEventRoles.objects.get(
                user=AuthUser(pk = getattr(self.request.user, 'id')),
                event_role__event_role_name='originator'
            )

        elif form.cleaned_data['is_originator'] is False and form.cleaned_data['event_room_id'] is not None:
            
            #responder
            user_event_role = UserEventRoles.objects.get(
                user=AuthUser(pk = getattr(self.request.user, 'id')),
                event_role__event_role_name='responder'
            )

        else:

            return JsonResponse({'message':'Missing required form data.'}, status=status.HTTP_400_BAD_REQUEST)

        #create event, excluding audio_file and event_room_id
        new_event = Events.objects.create(
            user_event_role=user_event_role,
            event_tone=EventTones(pk=form.cleaned_data['event_tone_id']),
        )

        if form.cleaned_data['is_originator'] is True:

            #create event_room row if user is originator
            new_event.event_room = EventRooms.objects.create(
                event_room_name=form.cleaned_data['event_room_name'],
            )

        else:

            #get specified event_room if user is responder
            new_event.event_room = EventRooms(pk=form.cleaned_data['event_room_id'])

        #save audio_file here to allow reference to model instance, as it now exists
        new_event.audio_file = form.cleaned_data['audio_file']

        new_event.save()

        #don't return super().form_valid(form), else it goes though form.save() again
        return JsonResponse(data={}, status=status.HTTP_201_CREATED)


#view specific event
#to fetch replies and create new reply, we use EventsByRoom viewset
class ViewSpecificEvents(FormView):

    template_name = 'voicewake/events/view_specific_events.html'
    form_class = CreateResponderEventsForm
    success_url = '/'

    def get(self, request, *args, **kwargs):

        #originator event
        #should always have only 1 per room
        try:

            originator_event = Events.objects.select_related(
                'event_room'
            ).get(
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
