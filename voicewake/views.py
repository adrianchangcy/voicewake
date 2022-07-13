from django import views
from django.http import JsonResponse, QueryDict
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, permission_required

#class-based view
from rest_framework import viewsets
    #ModelViewSet has: list, create, retrieve, update, partial_update, destroy
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic.edit import FormView
from django.views.generic.list import ListView

#Python libraries
from datetime import datetime, timezone, timedelta

from voicewake.forms import *

from .models import *
from .serializers import *


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


@login_required(login_url='/login')
def home(request):

    user_verification_options = UserVerificationOptions.objects.all()

    #HTML forms only accept GET and POST methods, hence this workaround for deletion
    if request.method == 'POST':

        user_verification_option_id = request.POST.get("delete_user_verification_option")
        
        if user_verification_option_id is not None:

            user_verification_option = UserVerificationOptions.objects.filter(id=user_verification_option_id).first()

            if user_verification_option:

                user_verification_option.delete()

                #redirect to remove 'confirm form submission' dialog on manual refresh
                return redirect('/')

    return render(request, 'voicewake/home.html', {"user_verification_options":user_verification_options})


def sign_up(request):

    if request.method == 'POST':

        #show filled form

        form = UserSignUpForm(request.POST)

        if form.is_valid():

            user = form.save()
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

#create event
class EventFormView(FormView):

    template_name = 'voicewake/create_event.html'
    form_class = CreateEventForm
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

        event_status = EventStatuses.objects.filter(event_status_name='available').first()

        #combine datetime then create schedule at separate table
        event_date = form.cleaned_data['event_date'].strftime('%Y-%m-%d')
        event_time = form.cleaned_data['event_time'].strftime('%H:%M:%S')
        event_datetime = event_date + ' ' + event_time

        #have to use .first() because model-based fields give .filter() QuerySet object
        new_event = Events.objects.create(
            user_event_role=user_event_role,
            event_name=form.cleaned_data['event_name'],
            event_purpose=form.cleaned_data['event_purpose'].first(),
            event_tone=form.cleaned_data['event_tone'].first(),
            event_message=form.cleaned_data['event_message'],
            language=form.cleaned_data['language'].first(),
            event_status=event_status,
            when_trigger=event_datetime,
        )

        #form currently does not handle EventRepeatDetails
        #only create new EventRepeatDetails obj in db if one of those columns are specified

        #to-do: please clarify that timezone adjustments are accurate

        #don't return super().form_valid(form), else it goes though form.save() again
        return redirect('/create-event')



class EventListView(ListView):

    template_name = 'voicewake/view_events.html'

    def get_queryset(self):

        user_event_role = UserEventRoles.objects.get(
                                                    user=self.request.user.id,
                                                    event_role__event_role_name='listener'
                                                    )

        # queryset = EventSchedules.objects.select_ related('event').filter(event__user_event_role=user_event_role)
        events = Events.objects.filter(user_event_role=user_event_role)

        print(events.values())
        return events

    
