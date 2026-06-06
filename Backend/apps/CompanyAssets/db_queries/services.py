from django.db import transaction

from . import selectors
from ..models import CompanyAssets, CompanyAssetsAttachments


@transaction.atomic
def update_company_asset(*, instance: CompanyAssets, validated_data: dict) -> CompanyAssets:
    for field, value in validated_data.items():
        setattr(instance, field, value)
    instance.save()
    return instance


@transaction.atomic
def create_asset_attachments(*, asset_id, files: list) -> list[CompanyAssetsAttachments]:
    asset = selectors.get_specific_company_asset_instance(asset_id)
    created = []
    for uploaded_file in files:
        attachment = CompanyAssetsAttachments(asset=asset, file=uploaded_file)
        attachment.save()
        created.append(attachment)
    return created
