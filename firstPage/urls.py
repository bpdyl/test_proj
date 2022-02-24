from django.urls import path
from firstPage.views import(
    send_request,
    cancel_request,
    ThreadViewSet,

)

app_name = "firstPage"

urlpatterns = [
    path('send_request/',send_request, name='send-friend-request'),
    path('cancel_request/',cancel_request, name = 'cancel-friend-request'),
    path('contact_list/',ThreadViewSet.as_view({'get': 'list'}),name = 'thread_view'),

]