import functools
from django.urls import reverse
from django.shortcuts import redirect
from django.http import JsonResponse
from rest_framework import status

from typing import Literal


#middleware is not suitable because the 'Accept' header is unreliable
#not all decorators need to run on every request and response



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

            if request.user.is_authenticated is True and request.user.is_banned is True:

                if return_instance == "response":

                    return JsonResponse(
                        data={
                            'message': 'This feature is not allowed for banned users.',
                        },
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                elif return_instance == "redirect" and request.path != redirect_url:

                    return redirect(redirect_url)

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





























