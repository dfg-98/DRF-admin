import sys

from django.contrib import admin

sys.path.append("..")
import dj_rest_admin

from .models import SecondTestModel, TestModel

# Register your models here.

dj_rest_admin.site.register(TestModel)
dj_rest_admin.site.register(SecondTestModel)
