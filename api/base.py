import abc
from typing import Callable, List, Type, Union

from django.contrib.auth import get_user_model
from django.db import models
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from spora_health.common.serializers import BaseSerializer

USER_MODEL = get_user_model()


class BaseProcessor(abc.ABC):
    # If you want to use object lookups other than pk, set 'lookup_field'.
    # For more complex lookup requirements override `get_object()`.
    lookup_field = "pk"
    lookup_url_kwarg = None

    def __init__(
        self,
        *,
        current_user: USER_MODEL,
        request_data: dict = None,
        url_params: dict,
        query_params: dict,
        filter_queryset: Callable[[models.QuerySet], models.QuerySet],
        paginate_queryset: Callable[[models.QuerySet], List[models.Model]],
        check_object_permissions: Callable[[models.Model], None],
        partial_update: bool = False,
    ) -> None:
        super().__init__()
        self._current_user = current_user
        self._request_data = request_data
        self._url_params = url_params
        self._query_params = query_params
        self._filter_queryset = filter_queryset
        self._paginate_queryset = paginate_queryset
        self._check_object_permissions = check_object_permissions
        self._partial_update = partial_update

    def check_object_permissions(self, obj: models.Model) -> None:
        self._check_object_permissions(obj)

    def get_object(self, queryset: models.QuerySet) -> models.Model:
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self._url_params, (
            "Expected view %s to be called with a URL keyword argument "
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            "attribute on the view correctly."
            % (self.__class__.__name__, lookup_url_kwarg)
        )

        filter_kwargs = {self.lookup_field: self._url_params[lookup_url_kwarg]}
        obj = get_object_or_404(queryset, **filter_kwargs)

        self.check_object_permissions(obj)

        return obj


class BaseCommandProcessor(BaseProcessor):
    def execute(self) -> Union[models.Model, dict]:
        """Execute command"""
        raise NotImplementedError()


class BaseQueryProcessor(BaseProcessor):
    model = None  # Required for filters
    paginated = True

    def execute(self) -> Union[models.Model, List[models.Model], dict, List[dict]]:
        """Execute query"""
        raise NotImplementedError()

    def filter_and_paginate_queryset(
        self, queryset: models.QuerySet
    ) -> List[models.Model]:
        """Filter and paginate queryset"""
        return self.paginate_queryset(self.filter_queryset(queryset))

    def paginate_queryset(self, queryset: models.QuerySet) -> List[models.Model]:
        """Paginate queryset"""
        return self._paginate_queryset(queryset)

    def filter_queryset(self, queryset: models.QuerySet) -> models.QuerySet:
        """Filter queryset"""
        return self._filter_queryset(queryset)


class BaseAPI(APIView):
    # You'll need to either set these attributes,
    # or override `get_queryset_class()`/`get_serializer_class()`/`get_command_class()`.
    command_class = None
    queryset_class = None
    serializer_class = None

    # The filter backend classes to use for queryset filtering
    filter_backends = api_settings.DEFAULT_FILTER_BACKENDS

    # The style to use for queryset pagination.
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    def get_processor_init(self) -> dict:
        """Processor init params"""
        return {
            "current_user": self.request.user,
            "url_params": self.kwargs,
            "query_params": self.request.GET,
            "filter_queryset": self.filter_queryset,
            "paginate_queryset": self.paginate_queryset,
            "check_object_permissions": self.check_instance_permissions,
        }

    def get_queryset_class(self) -> Type[BaseQueryProcessor]:
        assert self.queryset_class is not None, (
            "'%s' should either include a `queryset_class` attribute, "
            "or override the `get_queryest_class()` method." % self.__class__.__name__
        )

        return self.queryset_class

    def get_queryset(self, *args, **kwargs) -> BaseQueryProcessor:
        if getattr(self, "swagger_fake_view", False):
            # Queryset just for schema generation metadata
            return None

        queryset_class = self.get_queryset_class()
        default_kwargs = self.get_processor_init()
        default_kwargs.update(kwargs)
        return queryset_class(*args, **default_kwargs)

    def get_command_class(self) -> Type[BaseCommandProcessor]:
        assert self.command_class is not None, (
            "'%s' should either include a `command_class` attribute, "
            "or override the `get_command_class()` method." % self.__class__.__name__
        )

        return self.command_class

    def get_command(self, *args, **kwargs) -> BaseCommandProcessor:
        command_class = self.get_command_class()
        default_kwargs = self.get_processor_init()
        default_kwargs.update(kwargs)
        return command_class(*args, **default_kwargs)

    def get_serializer(self, *args, **kwargs) -> BaseSerializer:
        """
        Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.
        """
        serializer_class = self.get_serializer_class()
        kwargs.setdefault("context", self.get_serializer_context())
        return serializer_class(*args, **kwargs)

    def get_serializer_class(self) -> Type[BaseSerializer]:
        """
        Return the class to use for the serializer.
        Defaults to using `self.serializer_class`.
        You may want to override this if you need to provide different
        serializations depending on the incoming request.
        (Eg. admins get full serialization, others get basic serialization)
        """
        assert self.serializer_class is not None, (
            "'%s' should either include a `serializer_class` attribute, "
            "or override the `get_serializer_class()` method." % self.__class__.__name__
        )

        return self.serializer_class

    def get_serializer_context(self) -> dict:
        """
        Extra context provided to the serializer class.
        """
        return {"request": self.request, "format": self.format_kwarg, "view": self}

    def filter_queryset(self, queryset) -> models.QuerySet:
        """
        Given a queryset, filter it with whichever filter backend is in use.
        You are unlikely to want to override this method, although you may need
        to call it either from a list view, or from a custom `get_object`
        method if you want to apply the configured filtering backend to the
        default queryset.
        """
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    @property
    def paginator(self):
        """
        The paginator instance associated with the view, or `None`.
        """
        if not hasattr(self, "_paginator"):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        return self._paginator

    def paginate_queryset(self, queryset) -> List[dict]:
        """
        Return a single page of results, or `None` if pagination is disabled.
        """
        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(queryset, self.request, view=self)

    def get_paginated_response(self, data) -> Response:
        """
        Return a paginated style `Response` object for the given output data.
        """
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data)

    def check_instance_permissions(self, instance):
        return super().check_object_permissions(self.request, instance)

    @property
    def is_post_method(self):
        return self.request.method.lower() == "post"
