from django.urls import path
from .views import NotificationListView, MarkNotificationReadView, MarkAllAsReadView,UnreadNotificationCountView

urlpatterns = [
    path('list/', NotificationListView.as_view(), name='notification-list'),
    path('<int:pk>/read/', MarkNotificationReadView.as_view(), name='mark-read'),
    path('mark-all-read/', MarkAllAsReadView.as_view(), name='mark-all-read'),
    path('unread-count/', UnreadNotificationCountView.as_view(), name='unread-count'),
]