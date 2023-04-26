from dj_rest_admin import RestModelAdmin

from .models import SecondTestModel, TestModel


class TestRestModelAdmin(RestModelAdmin):
    pass


class SecondTestRestModelAdmin(RestModelAdmin):
    def get_queryset(self):
        queryset = SecondTestModel.objects.filter(age__lt=30)
        return queryset
