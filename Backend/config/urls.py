from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

third_party_urls = [
    path("ckeditor5/", include("django_ckeditor_5.urls")),
    path("site_administration/", admin.site.urls),
]

urlpatterns = [
    path("api/", include("apps.Users.urls")),
    path("api/registertion/", include("apps.registertion.urls")),
    path("api/transactions_log/", include("apps.TransactionsLog.urls")),
    path("api/projects/", include("apps.Projects.urls")),
    path("api/notifications/", include("apps.Notifications.urls")),
    path("api/expenses/", include("apps.Expenses.urls")),
    path("api/company_assets/", include("apps.CompanyAssets.urls")),
    path("api/safe/", include("apps.Safe.urls")),
    path("api/suppliers/", include("apps.Suppliers.urls")),
    path("api/quotations/", include("apps.Quotations.urls")),
    # path("api/reports/", include("apps.Reports.urls")),
    path("api/clients/", include("apps.Clients.urls")),
    path("api/dashboard/", include("apps.Dashboard.urls")),
    # Health check endpoint
    path("health/", lambda request: HttpResponse("OK")),
] + third_party_urls  # noqa
if settings.DEBUG:
    import debug_toolbar

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
