from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from config.env import ENVIRONMENT

SITE_URL = "<>"
DR_LOGO = "DR-mode-logo.png"
LI_LOGO = "logo_without_bg.png"
SITE_TITLE = "ProjectName"


def dashboard_callback(request, context):
    """
    Callback to prepare custom variables for index template which is used as dashboard template.
    """
    context.update(
        {
            "environment": ENVIRONMENT,  # Add the environment variable to the context
        }
    )
    return context


def badge_callback(request):
    return 3


UNFOLD = {
    "SITE_TITLE": SITE_TITLE,
    "SITE_HEADER": f"{SITE_TITLE}: {ENVIRONMENT}",
    "SITE_URL": f"{SITE_URL}/",
    "SITE_ICON": {
        "light": lambda request: static(f"{LI_LOGO}"),  # light mode
        "dark": lambda request: static(f"{DR_LOGO}"),  # dark mode
    },
    "SITE_SYMBOL": "speed",  # symbol from icon set
    # favicon configuration
    "SITE_FAVICONS": [
        {
            "rel": "icon",
            "sizes": "128x128",
            "type": "image/png",
            "href": lambda request: static(f"{DR_LOGO}"),
        },
        {
            "rel": "icon",
            "sizes": "192x192",
            "type": "image/png",
            "href": lambda request: static(f"{DR_LOGO}"),
        },
    ],
    "SHOW_VIEW_ON_SITE": True,  # show/hide "View on site" button, default: True
    # Environment-specific settings
    "ENVIRONMENT": ENVIRONMENT,
    "ENVIRONMENT_COLORS": {
        "development": "#2297AE",  # Your primary color for dev
        "staging": "#FFA500",  # Orange for staging
        "production": "#4CAF50",  # Green for production
    },
    # Callbacks
    "DASHBOARD_CALLBACK": dashboard_callback,
    # color scheme
    "COLORS": {
        "font": {
            "subtle-light": "107 114 128",
            "subtle-dark": "156 163 175",  # Better dark mode contrast
            "default-light": "55 65 81",  # Improved readability
            "default-dark": "229 231 235",  # Better dark mode text
            "important-light": "17 24 39",
            "important-dark": "#2297AE",  # Use your brand color for important elements
        },
        "primary": {
            "50": "#e6f7f9",
            "100": "#b3e9f0",
            "200": "#80dbe7",
            "300": "#4dcdde",
            "400": "#2297AE",  # Your main brand color
            "500": "#1a798c",
            "600": "#145b6a",
            "700": "#0e3d48",
            "800": "#081f26",
            "900": "#040f13",
        },
    },
    # sidebar
    "SIDEBAR": {
        "show_search": True,  # Enable search for better UX
        "show_all_applications": False,  # Better performance with collapsible groups
        "navigation": [
            {
                "title": _("Core"),
                "separator": True,
                "collapsible": False,  # Keep core items always visible
                "items": [
                    {
                        "title": _("Dashboard"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                        "permission": lambda request: request.user.is_authenticated,
                    },
                    {
                        "title": _("Site"),
                        "icon": "public",
                        "link": SITE_URL,  # Link to actual site
                        "target": "_blank",  # Open in new tab
                    },
                ],
            },
        ],
    },
    # Additional recommended settings
    "LOGIN": {
        "image": lambda request: static("admin-login-bg.jpg"),  # Custom login background
    },
    "STYLES": [
        lambda request: static("css/custom-admin.css"),  # Custom CSS
    ],
    "SCRIPTS": [
        lambda request: static("js/custom-admin.js"),  # Custom JS if needed
    ],
}
