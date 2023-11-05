import firebase_admin
from firebase_admin import credentials
from django.http import JsonResponse
from django.contrib.auth.models import User

# Initialize Firebase Admin SDK
cred = credentials.Certificate('D:/projects/FirebasePrivateKey/djangoassignment-769fb-firebase-adminsdk-9f3e4-ae05c3834e.json')
firebase_admin.initialize_app(cred)

class FirebaseAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Print request headers for debugging
        print("Request Headers:", request.META)

        # Check the custom_token in the request header and authenticate the user using Firebase SDK
        custom_token = request.META.get('HTTP_AUTHORIZATION')
        print("Custom Token: ", custom_token)

        if custom_token:
            decoded_token = firebase_admin.auth.verify_id_token(custom_token)
            print("Decoded Token:", decoded_token)
            request.user = User.objects.get(username=decoded_token['username'])
            # try:
            #     decoded_token = firebase_admin.auth.verify_id_token(custom_token)
            #     print("Decoded Token:", decoded_token)
            #     request.user = User.objects.get(username=decoded_token['username'])
            # except:
            #     return JsonResponse({'error': 'Unauthorized'}, status=401)

        response = self.get_response(request)
        return response