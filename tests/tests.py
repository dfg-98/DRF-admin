import pdb

from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.template.response import TemplateResponse
from django.test.client import RequestFactory
from django.urls import path, reverse
from rest_framework.permissions import IsAdminUser
from rest_framework.serializers import ModelSerializer
from rest_framework.settings import api_settings
from rest_framework.test import (
    APIRequestFactory,
    APITestCase,
    URLPatternsTestCase,
    override_settings,
)
from rest_framework.viewsets import ModelViewSet

from dj_rest_admin import RestModelAdmin, register
from dj_rest_admin.sites import AdminSite, AlreadyRegistered, NotRegistered
from tests.models import SecondTestModel, TestAbstractModel, TestModel
from tests.pagination import LargeResultsSetPagination
from tests.permissions import ReadOnly
from tests.restmodeladmin import SecondTestRestModelAdmin, TestRestModelAdmin
from tests.serializers import AdminSerializer

# Create your tests here.


class TestRegistration(APITestCase):
    def setUp(self):
        self.site = AdminSite()

    def test_plain_registration(self):
        self.site.register(TestModel)
        self.assertTrue(issubclass(self.site._registry[TestModel], ModelViewSet))
        viewset = self.site._registry[TestModel]
        self.site.unregister(TestModel)
        registry_viewset_objects = [
            registry_object[0] for registry_object in self.site.admin_router.registry
        ]
        self.assertFalse(viewset in registry_viewset_objects)
        self.assertEqual(self.site._registry, {})

    def test_unregistering_unregistered_model(self):
        with self.assertRaises(NotRegistered):
            self.site.unregister(TestModel)

    def test_prevent_double_registration(self):
        self.site.register(TestModel)
        with self.assertRaises(AlreadyRegistered):
            self.site.register(TestModel)

    def test_get_registry(self):
        self.site.register(TestModel)
        self.assertEqual(self.site._registry, self.site.get_registry())

    def test_abstract_model_registration(self):
        with self.assertRaises(ImproperlyConfigured):
            self.site.register(TestAbstractModel)

    def test_is_registered_registered_model(self):
        self.site.register(TestModel)
        self.assertTrue(self.site.is_registered(TestModel))

    def test_is_registered_unregistered_model(self):
        self.assertFalse(self.site.is_registered(TestModel))

    def test_iterable_registration(self):
        self.site.register([TestModel, SecondTestModel])
        self.assertTrue(issubclass(self.site._registry[TestModel], ModelViewSet))
        self.assertTrue(issubclass(self.site._registry[SecondTestModel], ModelViewSet))

    def test_custom_serializer_registration(self):
        self.site.register(TestModel, serializer_or_modeladmin=AdminSerializer)
        self.assertEqual(
            self.site._registry[TestModel].serializer_class, AdminSerializer
        )

    def test_custom_permission_class_registration(self):
        self.site.register(TestModel, permission_classes=[ReadOnly])
        self.assertEqual(self.site._registry[TestModel].permission_classes, [ReadOnly])

    def test_custom_pagination_class_registration(self):
        self.site.register(TestModel, pagination_class=LargeResultsSetPagination)
        self.assertEqual(
            self.site._registry[TestModel].pagination_class, LargeResultsSetPagination
        )

    def test_default_serializer_registration(self):
        self.site.register(TestModel)
        self.assertEqual(
            self.site._registry[TestModel].serializer_class.__name__,
            "TestModelSerializer",
        )

    def test_default_permission_class_registration(self):
        self.site.register(
            TestModel,
        )
        self.assertEqual(
            self.site._registry[TestModel].permission_classes, [IsAdminUser]
        )

    def test_default_pagination_class_registration(self):
        self.site.register(TestModel)
        self.assertEqual(
            self.site._registry[TestModel].pagination_class,
            api_settings.DEFAULT_PAGINATION_CLASS,
        )

    def test_restmodeladmin_registration(self):
        self.site.register(TestModel, TestRestModelAdmin)
        self.assertEqual(self.site._registry[TestModel], TestRestModelAdmin)

    def test_restmodeladmin_defaults(self):
        self.site.register(TestModel, TestRestModelAdmin)
        # Add some data
        for i in [10, 20, 30, 40, 50, 60]:
            TestModel.objects.create(age=i, name=str(i))
        self.assertQuerysetEqual(
            self.site._registry[TestModel].queryset,
            TestModel.objects.all(),
            ordered=False,
        )
        self.assertEqual(
            self.site._registry[TestModel].serializer_class.__name__,
            "TestModelSerializer",
        )

    def test_register_decorator(self):
        @register(TestModel, site=self.site)
        class DecoratorRestModelAdmin(RestModelAdmin):
            pass

        self.assertEqual(self.site._registry[TestModel], DecoratorRestModelAdmin)

    def test_register_decorator_with_serializer(self):
        @register(TestModel, site=self.site)
        class DecoratorSerializer(ModelSerializer):
            class Meta:
                model = TestModel
                fields = ["id"]

        self.assertEqual(
            self.site._registry[TestModel].serializer_class, DecoratorSerializer
        )

    def test_register_decorator_with_not_models(self):
        with self.assertRaises(ValueError):

            @register()
            class Foo:
                pass

    def test_register_decorator_with_invalid_admin_site(self):
        with self.assertRaises(ValueError):

            @register(TestModel, site=True)
            class Foo:
                pass

    def test_register_decorator_with_invalid_class(self):
        with self.assertRaises(ValueError):

            @register(TestModel)
            class Foo:
                pass


site = AdminSite()
site.register(TestModel)

register(SecondTestModel, site=site)(SecondTestRestModelAdmin)

urlpatterns = [path("test_admin/", site.urls), path("admin-docs/", site.docs)]


@override_settings(ROOT_URLCONF="tests.tests")
class TestViewSets(APITestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="super", password="secret", email="super@example.com"
        )
        self.client.force_login(self.superuser)

    def test_docs_generation(self):
        docs_url = reverse("api-docs:docs-index")
        response = self.client.get(docs_url)
        self.assertIn("TestModel", response.data)
        self.assertEqual(response.status_code, 200)

    def test_list_model_objects(self):
        url = reverse("restadmin:admin_TestModel-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_model_endpoint(self):
        url = reverse("restadmin:admin_TestModel-list")
        response = self.client.post(url, data={"name": "name", "age": 16})
        self.assertEqual(TestModel.objects.count(), 1)
        self.assertEqual(response.status_code, 201)

    def test_update_model_endpoint(self):
        model_object = TestModel.objects.create(name="name1", age=5)
        url = reverse("restadmin:admin_TestModel-detail", args=(model_object.id,))
        response = self.client.put(url, data={"name": "name2", "age": 15})
        new_object = TestModel.objects.get(id=model_object.id)
        self.assertEqual(new_object.age, 15)
        self.assertEqual(new_object.name, "name2")

    def test_partial_update_model_endpoint(self):
        model_object = TestModel.objects.create(name="name1", age=5)
        url = reverse("restadmin:admin_TestModel-detail", args=(model_object.id,))
        response = self.client.patch(url, data={"age": 15})
        new_object = TestModel.objects.get(id=model_object.id)
        self.assertEqual(new_object.age, 15)

    def test_get_model_endpoint(self):
        model_object = TestModel.objects.create(name="name1", age=5)
        url = reverse("restadmin:admin_TestModel-detail", args=(1,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_delete_model_endpoint(self):
        model_object = TestModel.objects.create(name="name1", age=5)
        self.assertEqual(TestModel.objects.count(), 1)
        url = reverse("restadmin:admin_TestModel-detail", args=(1,))
        response = self.client.delete(url)
        self.assertEqual(TestModel.objects.count(), 0)

    def test_restmodeladmin_list_objects(self):
        # Add some data
        for i in [10, 20, 30, 40, 50, 60]:
            SecondTestModel.objects.create(age=i, name=str(i))
        url = reverse("restadmin:admin_SecondTestModel-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)

    def test_restmodeladmin_create_model_endpoint(self):
        url = reverse("restadmin:admin_SecondTestModel-list")
        response = self.client.post(url, data={"name": "name", "age": 16})
        self.assertEqual(SecondTestModel.objects.count(), 1)
        self.assertEqual(response.status_code, 201)

    def test_restmodeladmin_update_model_endpoint(self):
        model_object = SecondTestModel.objects.create(name="name1", age=5)
        url = reverse("restadmin:admin_SecondTestModel-detail", args=(model_object.id,))
        response = self.client.put(url, data={"name": "name2", "age": 15})
        new_object = SecondTestModel.objects.get(id=model_object.id)
        self.assertEqual(new_object.age, 15)
        self.assertEqual(new_object.name, "name2")

    def test_restmodeladmin_partial_update_model_endpoint(self):
        model_object = SecondTestModel.objects.create(name="name1", age=5)
        url = reverse("restadmin:admin_SecondTestModel-detail", args=(model_object.id,))
        response = self.client.patch(url, data={"age": 15})
        new_object = SecondTestModel.objects.get(id=model_object.id)
        self.assertEqual(new_object.age, 15)
