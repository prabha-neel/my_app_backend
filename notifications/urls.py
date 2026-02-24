from django.urls import path
from .views import NotificationListView, MarkNotificationReadView, MarkAllAsReadView,UnreadNotificationCountView

urlpatterns = [
    # Path khali rakho taaki /api/v1/notifications/ par ye chale
    path('', NotificationListView.as_view(), name='notification-list'),
    path('<int:pk>/read/', MarkNotificationReadView.as_view(), name='mark-read'),
    path('mark-all-read/', MarkAllAsReadView.as_view(), name='mark-all-read'),
    path('unread-count/', UnreadNotificationCountView.as_view(), name='unread-count'),
]