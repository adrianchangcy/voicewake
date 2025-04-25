import functools
from django.urls import reverse
from django.shortcuts import redirect
from django.http import JsonResponse
from rest_framework import status

from typing import Literal
from voicewake.services import get_datetime_now



#middleware is not suitable because the 'Accept' header is unreliable
#not all decorators need to run on every request and response

#reminder
    #@decorators run from closest decorator to function, to furthest
    #but if passing decorators as [] in @method_decorator, it runs from first to last in []



def deny_if_not_logged_in(return_instance:Literal["redirect"]):

    if return_instance not in ["redirect"]:

        raise ValueError("Invalid return_instance.")
    
    
    def decorator(passed_function):

        @functools.wraps(passed_function)
        def inner(request, *args, **kwargs):

            redirect_url = reverse('log_in')

            if request.user.is_authenticated is False and request.path != redirect_url:

                #you can use Django's messages to insert data at template
                #allows you to do "redirect back to page when done", and toasts
                return redirect(redirect_url)

            return passed_function(request, *args, **kwargs)
        
        return inner
    
    return decorator



def deny_if_already_logged_in(return_instance:Literal["response", "redirect"]):

    if return_instance not in ["response", "redirect"]:

        raise ValueError("Invalid return_instance.")
    
    
    def decorator(passed_function):

        @functools.wraps(passed_function)
        def inner(request, *args, **kwargs):

            redirect_url = reverse('home')

            if request.user.is_authenticated is True:

                if return_instance == "response":

                    return JsonResponse(
                        data={
                            'message': 'You are already logged in.',
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )
                
                elif return_instance == "redirect" and request.path != redirect_url:

                    return redirect(redirect_url)

            return passed_function(request, *args, **kwargs)
        
        return inner
    
    return decorator



def deny_if_banned(return_instance:Literal["response", "redirect"]):

    if return_instance not in ["response", "redirect"]:

        raise ValueError("Invalid return_instance.")
    
    
    def decorator(passed_function):

        @functools.wraps(passed_function)
        def inner(request, *args, **kwargs):

            redirect_url = reverse('user_banned')

            if request.user.is_authenticated is False or request.user.banned_until is None:

                pass

            elif request.user.banned_until > get_datetime_now():

                #user is still banned

                if return_instance == "response":

                    return JsonResponse(
                        data={
                            'message': 'This feature is not allowed for banned users.',
                        },
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                elif return_instance == "redirect" and request.path != redirect_url:

                    return redirect(redirect_url)
                
            elif request.user.banned_until <= get_datetime_now():

                #can unban

                #doing unban here will not guarantee it being done in a timely banner
                #because decorators are triggered by requests
                #but it is good enough for this context, since most APIs use this decorator
                request.user.banned_until = None
                request.user.save()

            return passed_function(request, *args, **kwargs)
        
        return inner
    
    return decorator



def deny_if_no_username(return_instance:Literal["response", "redirect"]):

    if return_instance not in ["response", "redirect"]:

        raise ValueError("Invalid return_instance.")
    
    
    def decorator(passed_function):

        @functools.wraps(passed_function)
        def inner(request, *args, **kwargs):

            redirect_url = reverse('set_username')

            if request.user.is_authenticated is True and request.user.username is None:

                if return_instance == "response":
                    
                    return JsonResponse(
                        data={
                            'message': 'Please set your username before continuing.',
                        },
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                elif return_instance == "redirect" and request.path != redirect_url:

                    return redirect(redirect_url)

            return passed_function(request, *args, **kwargs)
        
        return inner
    
    return decorator



def deny_if_not_superuser(return_instance:Literal["response"]):

    if return_instance not in ["response"]:

        raise ValueError("Invalid return_instance.")
    
    
    def decorator(passed_function):

        @functools.wraps(passed_function)
        def inner(request, *args, **kwargs):

            if request.user.is_authenticated is False or request.user.is_superuser is False:

                return JsonResponse(
                    data={
                        'message': 'This feature is only allowed for superusers.',
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

            return passed_function(request, *args, **kwargs)
        
        return inner
    
    return decorator





































