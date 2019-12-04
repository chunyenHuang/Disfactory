import json
from datetime import datetime

from rest_framework.decorators import api_view

from django.db import transaction
from django.http import JsonResponse
from django.conf import settings
from django.contrib.gis.geos import Point

from ..models import Factory, ReportRecord
from ..serializers import FactorySerializer

from .utils import _get_client_ip

import logging
logger = logging.getLogger('django')


#@api_view(['PUT'])
def update_factory_attribute(request, factory_id):
    client_ip = _get_client_ip(request)
    put_body = json.loads(request.body)
    serializer = FactorySerializer(data=put_body, partial=True)

    if not serializer.is_valid():
        logger.warning(f" {client_ip} : <serializer errors> ")
        return JsonResponse(
            serializer.errors,
            status=400,
        )

    updated_factory_fields = put_body.copy()
    updated_factory_fields.pop("others", None)
    updated_factory_fields.pop("contact", None)

    new_lng = put_body.get("lng")
    new_lat = put_body.get("lat")
    if (new_lat is not None) or (new_lng is not None):
        factory = Factory.objects.only("lat", "lng").get(pk=factory_id)
        new_lng = new_lng or factory.lng
        new_lat = new_lat or factory.lat
        new_point = Point(new_lng, new_lat, srid=4326)
        new_point.transform(settings.POSTGIS_SRID)
        updated_factory_fields["point"] = new_point

    if "status" in put_body:
        updated_factory_fields["status_time"] = datetime.now()

    new_report_record_fields = {
        "factory_id": factory_id,
        "user_ip": client_ip,
        "action_type": "UPDATE",
        "action_body": put_body,
        "contact": put_body.get("contact"),
        "others": put_body.get("others", ""),
    }

    with transaction.atomic():
        Factory.objects.filter(pk=factory_id).update(**upfactorydated_factory_fields)
        ReportRecord.objects.create(**new_report_record_fields)
        factory = Factory.objects.get(pk=factory_id)

    logger.info(f" {user_ip} : <Update factory> {factory_id} {put_body} ")
    serializer = FactorySerializer(factory)
    return JsonResponse(serializer.data, safe=False)
