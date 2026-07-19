from .collector import collect_cloud_resources

from .localstack import (
    get_s3_client,
    get_ec2_client,
    get_iam_client,
)

from .normalizer import (
    normalize_resource,
    normalize_resources,
)

__all__ = [

    "collect_cloud_resources",

    "normalize_resource",

    "normalize_resources",

    "get_s3_client",

    "get_ec2_client",

    "get_iam_client",
]