from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),

    # UC-04 Login, UC-05 Register Farm/Account, employee management
    path("api/auth/", include("accounts.urls")),

    path("api/farms/", include("farms.urls")),
    path("api/batches/", include("batches.urls")),
    path("api/feed/", include("feed.urls")),
    path("api/health/", include("health.urls")),
    path("api/sales/", include("sales.urls")),

    # UC-01/02/03 — AI-backed endpoints (chick counting, mortality, price prediction)
    path("api/monitoring/", include("monitoring.urls")),

    # UC-08 Alerts
    path("api/alerts/", include("alerts.urls")),

    # UC-07 View Dashboard
    path("api/dashboard/", include("dashboard.urls")),

    # UC-09 Chatbot Interaction
    path("api/chatbot/", include("chatbot.urls")),

    # AI inference engine health/status
    path("api/ai/", include("ai_integration.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
