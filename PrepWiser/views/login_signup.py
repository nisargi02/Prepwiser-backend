from django.contrib.auth import authenticate
from rest_framework import views, status, response
from .serializers import UserSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

class SignUpView(views.APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            user_data = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                "message": "User successfully registered",
                "user_id": user.id,  # Provide the user ID or any other relevant info
                "email": user.email,
                "first_name": user.first_name  # Assuming get_full_name() is appropriate for your model
            }
            return response.Response(user_data, status=status.HTTP_201_CREATED)
        return response.Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(views.APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(username=email, password=password)  # Ensure correct keyword argument is used
        if user:
            refresh = RefreshToken.for_user(user)
            user_data = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                "message": "User Authenticated",
                "first_name": user.first_name,  # or user.first_name if you just want the first name
                "email": user.email  # You might also want to include the email or other data
            }
            
            return response.Response(user_data, status=status.HTTP_200_OK)
        else:
            return response.Response({"message": "Invalid Credentials"}, status=status.HTTP_401_UNAUTHORIZED)