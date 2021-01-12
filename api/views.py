from rest_framework import status
from rest_framework.response import Response

from .base import BaseAPI
from .exceptions import ApiErrorsMixin
from .mixins import (
    CreateAPIMixin,
    DestroyAPIMixin,
    ListAPIMixin,
    RetrieveAPIMixin,
    UpdateAPIMixin,
)


class GenericAPI(ApiErrorsMixin, BaseAPI):
    pass


class CreateAPI(CreateAPIMixin, GenericAPI):
    def post(self, request, *args, **kwargs):
        response_data = self.create(request, *args, **kwargs)
        headers = self.get_success_headers(response_data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)


class ListAPI(ListAPIMixin, GenericAPI):
    def get(self, request, *args, **kwargs):
        response_data, is_paginated = self.list(request, *args, **kwargs)

        if is_paginated:
            return self.get_paginated_response(response_data)

        return Response(response_data)


class RetrieveAPI(RetrieveAPIMixin, GenericAPI):
    def get(self, request, *args, **kwargs):
        response_data = self.retrieve(request, *args, **kwargs)
        return Response(response_data)


class DestroyAPI(DestroyAPIMixin, GenericAPI):
    def delete(self, request, *args, **kwargs):
        self.destroy(request, *args, **kwargs)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UpdateAPI(UpdateAPIMixin, GenericAPI):
    def put(self, request, *args, **kwargs):
        response_data = self.update(request, *args, **kwargs)
        return Response(response_data)

    def patch(self, request, *args, **kwargs):
        response_data = self.partial_update(request, *args, **kwargs)
        return Response(response_data)


class ListCreateAPI(ListAPIMixin, CreateAPIMixin, GenericAPI):
    def get(self, request, *args, **kwargs):
        response_data, is_paginated = self.list(request, *args, **kwargs)

        if is_paginated:
            return self.get_paginated_response(response_data)

        return Response(response_data)

    def post(self, request, *args, **kwargs):
        response_data = self.create(request, *args, **kwargs)
        headers = self.get_success_headers(response_data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)


class RetrieveUpdateAPI(RetrieveAPIMixin, UpdateAPIMixin, GenericAPI):
    def get(self, request, *args, **kwargs):
        response_data = self.retrieve(request, *args, **kwargs)
        return Response(response_data)

    def put(self, request, *args, **kwargs):
        response_data = self.update(request, *args, **kwargs)
        return Response(response_data)

    def patch(self, request, *args, **kwargs):
        response_data = self.partial_update(request, *args, **kwargs)
        return Response(response_data)


class RetrieveDestroyAPI(RetrieveAPIMixin, DestroyAPIMixin, GenericAPI):
    def get(self, request, *args, **kwargs):
        response_data = self.retrieve(request, *args, **kwargs)
        return Response(response_data)

    def delete(self, request, *args, **kwargs):
        self.destroy(request, *args, **kwargs)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RetrieveUpdateDestroyAPI(
    RetrieveAPIMixin, UpdateAPIMixin, DestroyAPIMixin, GenericAPI
):
    def get(self, request, *args, **kwargs):
        response_data = self.retrieve(request, *args, **kwargs)
        return Response(response_data)

    def put(self, request, *args, **kwargs):
        response_data = self.update(request, *args, **kwargs)
        return Response(response_data)

    def patch(self, request, *args, **kwargs):
        response_data = self.partial_update(request, *args, **kwargs)
        return Response(response_data)

    def delete(self, request, *args, **kwargs):
        self.destroy(request, *args, **kwargs)
        return Response(status=status.HTTP_204_NO_CONTENT)
