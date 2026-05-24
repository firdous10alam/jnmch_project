from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import home

urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),

    # Frontend pages
    path("accounts/", include("accounts.urls")),
    path("reports/", include("reports.urls")),

    # APIs
    path("api/accounts/", include("accounts.api_urls")),
    path("api/otp/", include("otp.urls")),
    path("api/reports/", include("reports.api_urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
