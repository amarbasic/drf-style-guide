# DRF Style Guide

Django Rest Framework Style Guide

Based on DRF generics


## Example

Serializer class
```
class ItemSerializer(BaseSerializer):
  id = serializers.IntegerField()
  name = serializers.CharField()
```

Command class
```
class ItemCreateCommandProcessor(BaseCommandProcessor):
  model = Item
  
  def execute(self):
    return model.objects.create(**self._request_data)
```

Query class
```
class ItemQueryProcessor(BaseQueryProcessor):
  model = Item
  
  def execute(self):
    return self.filter_and_paginate_queryset(self.model.objects.all())
```

API class
```
class ItemListCreateAPI():
  serializer_class = ItemSerailizer
  command_class = ItemCreateCommandProcessor
  queryset_class = ItemListQueryProcessor
```
