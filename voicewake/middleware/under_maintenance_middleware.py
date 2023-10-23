from django.urls import reverse
from django.shortcuts import redirect
from django.http import JsonResponse
from rest_framework import status

class UnderMaintenanceMiddleware(object):

    def __init__(self, get_response):

        self.get_response = get_response


    def __call__(self, request):

        redirect_url = reverse('under_maintenance')

        if '/api/' in request.path:

            return JsonResponse(
                data={
                    'message': 'Server is under maintenance.',
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        elif request.path != redirect_url:

            return redirect(redirect_url)

        response = self.get_response(request)

        return response