"""
normalizer.py

Phase-4
Member-1

Normalizes raw AWS(LocalStack) resources into the common schema
expected by the existing Rule Engine.

Flow

Raw boto3 Response
        │
        ▼
 normalize_resource()
        │
        ▼
 resource_mapper.py
        │
        ▼
 Rule Engine Contract

The Rule Engine expects every resource to contain at least:

{
    "resource_id": "...",
    "resource_type": "..."
}

plus resource-specific attributes.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from .resource_mapper import map_resource

logger = logging.getLogger(__name__)


# ==========================================================
# Generic Normalizer
# ==========================================================

def normalize_resource(
    resource_type: str,
    *args,
    **kwargs,
) -> Dict[str, Any]:
    """
    Normalize a single cloud resource.

    Parameters
    ----------
    resource_type : str

    Returns
    -------
    dict
        Rule Engine compatible resource.
    """

    logger.info(
        "Normalizing resource type: %s",
        resource_type,
    )

    normalized = map_resource(
        resource_type,
        *args,
        **kwargs,
    )

    if "resource_id" not in normalized:

        raise ValueError(
            "Normalized resource missing resource_id"
        )

    if "resource_type" not in normalized:

        raise ValueError(
            "Normalized resource missing resource_type"
        )

    logger.debug(
        "Normalized Resource: %s",
        normalized,
    )

    return normalized


# ==========================================================
# Batch Normalizer
# ==========================================================

def normalize_resources(resources):
    """
    Normalize multiple resources.

    Parameters
    ----------
    resources

        Iterable containing tuples

        Example

        (
            "s3_bucket",
            bucket_name,
            bucket_acl
        )

    Returns
    -------
    list
    """

    normalized_resources = []

    for resource in resources:

        resource_type = resource[0]

        args = resource[1:]

        normalized_resources.append(

            normalize_resource(

                resource_type,

                *args,
            )

        )

    logger.info(

        "Normalized %d resources.",

        len(normalized_resources)

    )

    return normalized_resources