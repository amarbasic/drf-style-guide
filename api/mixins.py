from typing import Tuple

from rest_framework.settings import api_settings

from .base import BaseCommandProcessor, BaseQueryProcessor


class CreateAPIMixin:
    def create(self, request, *args, **kwargs) -> dict:
        """Action for POST method"""
        request_serializer = self.get_serializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        command: BaseCommandProcessor = self.get_command(
            request_data=request_serializer.validated_data
        )
        command_response = command.execute()
        response_serializer = self.get_serializer(command_response)

        return response_serializer.data

    def get_success_headers(self, data):
        try:
            return {"Location": str(data[api_settings.URL_FIELD_NAME])}
        except (TypeError, KeyError):
            return {}


class ListAPIMixin:
    def list(self, request, *args, **kwargs) -> Tuple[dict, bool]:
        """Action for GET method"""
        query: BaseQueryProcessor = self.get_queryset()
        queryset = query.execute()

        serializer = self.get_serializer(queryset, many=True)

        return serializer.data, query.paginated


class RetrieveAPIMixin:
    def retrieve(self, request, *args, **kwargs) -> dict:
        """Action for GET method"""
        query: BaseQueryProcessor = self.get_queryset()
        instance = query.execute()
        serializer = self.get_serializer(instance)
        return serializer.data


class UpdateAPIMixin:
    def update(self, request, *args, **kwargs) -> dict:
        """Action for PUT method"""
        partial = kwargs.pop("partial", False)
        request_serializer = self.get_serializer(data=request.data, partial=partial)
        request_serializer.is_valid(raise_exception=True)

        command: BaseCommandProcessor = self.get_command(
            request_data=request_serializer.validated_data, partial_update=partial
        )
        command_response = command.execute()
        response_serializer = self.get_serializer(command_response)

        return response_serializer.data

    def partial_update(self, request, *args, **kwargs):
        """Action for PATCH method"""
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)


class DestroyAPIMixin:
    def destroy(self, request, *args, **kwargs):
        """Action for DELETE method"""
        command = self.get_command()
        command.execute()
