from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .models import Profile
from .serializers import ProfileSerializer
import random
import string
import firebase_admin
from firebase_admin import credentials, auth
from django.http import JsonResponse


def generate_unique_username(first_name):
    # Generate a random string of characters
    random_suffix = ''.join(random.choices(string.ascii_lowercase, k=6))

    # Combine the first name and random suffix to create a unique username
    username = f'{first_name.lower()}{random_suffix}'

    # Check if the generated username already exists, and if so, regenerate it
    while User.objects.filter(username=username).exists():
        random_suffix = ''.join(random.choices(string.ascii_lowercase, k=6))
        username = f'{first_name.lower()}{random_suffix}'

    return username



# View for user registration
@csrf_exempt
@api_view(['POST'])
def register_view(request):
    if request.method == 'POST':
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')

        if not (username and email and password):
            return JsonResponse({'error': 'Email and password are required.'}, status=400)

        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'A user with that username already exists.'}, status=400)

        if len(password) < 8:
            return JsonResponse({'error': 'This password is too short. It must contain at least 8 characters.'}, status=400)

        # Generate a unique username based on the first name
        generated_username = generate_unique_username(first_name)
        
        user = User(username=generated_username, email=email,first_name=first_name,last_name=last_name)
        user.set_password(password)
        user.save()

        try:
            # Use the user's username as the UID in Firebase
            user_data = auth.create_user(
                uid=user.username,
                email=email,
                password=password,
                display_name=generated_username
            )
            # You can add more attributes to the user_data dictionary as needed

            return JsonResponse({'username': user.username, 'email': user.email})
        except Exception as e:
            # Handle the Firebase user creation error
            return JsonResponse({'error': f'Failed to create Firebase user: {str(e)}'}, status=400)

    return JsonResponse({'error': 'Invalid request method.'}, status=405)



# View for user login
@csrf_exempt
@api_view(['POST'])
def login_view(request):
    if request.method == 'POST':
        username = request.data.get('username')
        password = request.data.get('password')

        if not (username and password):
            return JsonResponse({'error': 'Username and password are required.'}, status=400)

        user = authenticate(request, username=username, password=password)
        print("username:",username)

        if user is not None:
            custom_token = auth.create_custom_token(user.username)
            print("username:", user.username)
            print("username:", custom_token)
            

            return JsonResponse({'username': user.username, 'email': user.email, 'full_name': f'{user.first_name} {user.last_name}', 'custom_token': custom_token.decode('utf-8')})
        else:
            return JsonResponse({'error': 'Invalid username or password.'}, status=400)

# View for viewing the profile
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_profile(request):
    print("token:")
    user = request.user
    profile = Profile.objects.get(user=user)
    serializer = ProfileSerializer(profile)
    return JsonResponse(serializer.data)

# View for editing the profile
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def edit_profile(request):
    user = request.user
    first_name = request.data.get('first_name', user.first_name)
    last_name = request.data.get('last_name', user.last_name)
    username = request.data.get('username', user.username)

    # Check for username uniqueness if it's edited
    if username != user.username and User.objects.filter(username=username).exists():
        return JsonResponse({'error': f'User already exists with the username {username}'}, status=400)

    user.first_name = first_name
    user.last_name = last_name
    user.username = username
    user.save()

    return JsonResponse({'username': user.username, 'email': user.email, 'full_name': f'{user.first_name} {user.last_name}'})