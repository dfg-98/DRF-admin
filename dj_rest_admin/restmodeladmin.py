from rest_framework.permissions import IsAdminUser
from rest_framework.viewsets import ModelViewSet


class RestModelAdmin(ModelViewSet):
    """Equivalent to ModelAdmin, behave like a ModelViewSet

    This class is an abstraction layer between this packages
    and using vanilla ModelViewSet. This will allow implementing
    more features in the future
    """

    permission_classes = [IsAdminUser]  # By default allow admin users only
