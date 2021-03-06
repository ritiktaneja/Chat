from django.conf import settings
from django.contrib.auth import (
    login, logout, user_logged_in, user_logged_out, get_user_model,
    authenticate,
)
from django.http import JsonResponse
from django.utils.crypto import get_random_string
from django.utils.datastructures import MultiValueDictKeyError
from django.views.decorators.csrf import csrf_exempt

from rest_framework import permissions, status
from rest_framework.decorators import  api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import  APIView

from ..utils import (
    decode_jwt, get_ghost_user, get_jwt, verify_jwt,
)
from ..permissions import IsNotReservedUserName
from ..models import Chat, Message

User = get_user_model()


def get_user_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    else:
        return request.META.get('REMOTE_ADDR')


class UserRegisterView(APIView):
    authentication_classes = []
    permission_classes = [IsNotReservedUserName, ]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request, *args, **kwargs):
        try:
            username = request.POST['username']
            password = request.POST['password']
            email = request.POST['email']
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email
            )
            # marking as verified user
            user.userprofile.is_verified = True
            user.save()
            return Response(
                data={
                    'username': username,
                    'password': password, 'email': email,
                }, status=status.HTTP_201_CREATED
            )
        except MultiValueDictKeyError as e:
            if settings.DEBUG:
                print(e)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            if settings.DEBUG:
                print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifiedUserLoginView(APIView):
    authentication_classes = []
    permission_classes = [IsNotReservedUserName, ]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request):
        try:
            # authenticate the user
            user = authenticate(
                request, username=request.POST['username'],
                password=request.POST['password']
            )
            if user is not None:
                # login the user
                login(request, user)
                ip = get_user_ip(request)
                payload = {'username': user.username, 'ip': ip}
                token = get_jwt(payload)
                return Response(
                    data={
                          'token': token,
                          'verified': True,
                    }, status=status.HTTP_200_OK
                )
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            if settings.DEBUG:
                print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UnverifiedUserLoginView(APIView):
    authentication_classes = []
    permission_classes = [IsNotReservedUserName, ]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request):
        username = request.POST['username']
        if not User.objects.filter(username=username).exists():
            try:
                # creating new user with random password
                password = get_random_string(8)
                user = User.objects.create_user(
                    username=username,
                    password=password
                )
                # loggin the new user to save credentials in session
                login(request, user)
                # Every user to be added to the main chat
                user.user_chats.add(Chat.objects.get(uri=settings.RESERVED_URI['main']))
                # getting the user IP
                ip = get_user_ip(request)
                token = get_jwt({'username': username, 'ip': ip})
                return Response(
                    data={
                        'user': {
                            'username': username,
                            'token': token,
                        },'verified': False
                    }, status=status.HTTP_200_OK
                )
            except Exception as e:
                if settings.DEBUG:
                    print(e)
                return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(
                data={'error': True, 'message': 'User already exists!'},
                status=status.HTTP_200_OK
                )


class LogoutView(APIView):
    authentication_classes = []
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self ,request, *args, **kwargs):
        token = request.POST['token']
        payload = decode_jwt(token)
        username = payload['username']
        user = User.objects.get(username=username)
        # un-vreified user
        if not user.userprofile.is_verified:
            # call logout() to remove session data
            logout(request)
            try:
                user = User.objects.get(username=username)
                # marking user msgs as Ghosted-msg
                ghost_user = get_ghost_user()
                user_msgs = user.user_messages.all()
                for msg in user_msgs:
                    msg.sender = ghost_user
                    msg.save()
                # deleting user instance
                user.delete()
                return Response(
                    data={'username': username,},
                    status=status.HTTP_204_NO_CONTENT
                )
            except Exception as e:
                if settings.DEBUG:
                    print("Error in CustomLogoutView.\n", e)
                return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # verified user
        else:
            # logging out the user
            user_logged_out.send(
            sender=request.user.__class__, request=request, user=request.user
            )
            logout(request)
            return Response(
                data={'username': username,},
                status=status.HTTP_200_OK
            )


@api_view(['POST'])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def verify_token(request):
    if request.method == 'POST':
        username = request.POST['username']
        token = request.POST['token']
        if verify_jwt(token, username):
            return Response(
                {'verified': True},
            )
        else:
            return Response(
                {'verified': False},
            )
