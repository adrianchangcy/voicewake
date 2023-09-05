import functools
from django.urls import reverse
from django.shortcuts import redirect
from rest_framework.response import Response
from rest_framework import status



#need redirect_... and disable_api_... decorators of the same tasks
#because some views are for DRF while some are for normal pages
#and most importantly, I could not find a way to pass any "is_api" arg into decorators, due to the nature of decorators



def redirect_if_already_logged_in(passed_function):

    @functools.wraps(passed_function)
    def inner(request, *args, **kwargs):

        redirect_url = reverse('home')

        if request.user.is_authenticated is True and request.path != redirect_url:

            return redirect(redirect_url)

        return passed_function(request, *args, **kwargs)

    return inner


def disable_api_if_already_logged_in(passed_function):

    @functools.wraps(passed_function)
    def inner(request, *args, **kwargs):

        if request.user.is_authenticated is True:

            return Response(
                data={
                    'message': 'You are already logged in.',
                },
                status=status.HTTP_403_FORBIDDEN
            )

        return passed_function(request, *args, **kwargs)

    return inner


def redirect_if_banned(passed_function):

    @functools.wraps(passed_function)
    def inner(request, *args, **kwargs):

        redirect_url = reverse('user_banned')

        if request.user.is_authenticated is True and request.user.is_banned is True and request.path != redirect_url:

            return redirect(redirect_url)

        return passed_function(request, *args, **kwargs)

    return inner


def disable_api_if_banned(passed_function):

    @functools.wraps(passed_function)
    def inner(request, *args, **kwargs):

        if request.user.is_authenticated is True and request.user.is_banned is True:

            return Response(
                data={
                    'message': 'This feature is not allowed for banned users.',
                },
                status=status.HTTP_403_FORBIDDEN
            )

        return passed_function(request, *args, **kwargs)

    return inner


def redirect_if_no_username(passed_function):

    @functools.wraps(passed_function)
    def inner(request, *args, **kwargs):

        redirect_url = reverse('set_username')

        if request.user.is_authenticated is True and request.user.username_lowercase is None and request.path != redirect_url:

            return redirect(redirect_url)

        return passed_function(request, *args, **kwargs)

    return inner


def disable_api_if_no_username(passed_function):

    @functools.wraps(passed_function)
    def inner(request, *args, **kwargs):

        if request.user.is_authenticated is True and request.user.username_lowercase is None:

            return Response(
                data={
                    'message': 'Please set your username before continuing.',
                },
                status=status.HTTP_403_FORBIDDEN
            )

        return passed_function(request, *args, **kwargs)

    return inner







