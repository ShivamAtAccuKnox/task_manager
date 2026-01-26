from django.contrib import admin
from django.urls import path, include

# Docs
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

# Auth (JWT)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)


from project.views import RegisterView

urlpatterns = [
    # 1. Admin
    #path("api/auth/",include('rest_framework.urls')),
    path('admin/', admin.site.urls),
    path('api/silk/', include('silk.urls', namespace='silk')),

    # 2. Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # 3. Authentication
    path('api/auth/register/', RegisterView.as_view(), name='auth_register'),
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # 4. App Endpoints (Projects & Tasks)
    path('api/', include('project.urls')), 
]