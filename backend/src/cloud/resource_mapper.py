"""
resource_mapper.py

Converts raw AWS(LocalStack) responses into the resource schema
expected by the existing Phase-1 Rule Engine.

Rule Engine Contract
--------------------

S3 Bucket
{
    "resource_id": "...",
    "resource_type": "s3_bucket",
    "public_read": True,
    "public_write": False
}

Security Group
{
    "resource_id": "...",
    "resource_type": "security_group",
    "ingress": {
        "cidr": "0.0.0.0/0"
    }
}

IAM Policy
{
    "resource_id": "...",
    "resource_type": "iam_policy",
    "action": "s3:*"
}
"""

from __future__ import annotations

from typing import Any, Dict, List


# ==========================================================
# S3
# ==========================================================

def map_s3_bucket(
    bucket_name: str,
    acl: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Convert S3 bucket ACL into Rule Engine format.
    """

    public_read = False
    public_write = False

    grants = acl.get("Grants", [])

    for grant in grants:

        grantee = grant.get("Grantee", {})

        uri = grantee.get("URI", "")

        permission = grant.get("Permission", "")

        if "AllUsers" not in uri:
            continue

        if permission in ("READ", "FULL_CONTROL"):

            public_read = True

        if permission in ("WRITE", "FULL_CONTROL"):

            public_write = True

    return {

        "resource_id": bucket_name,

        "resource_type": "s3_bucket",

        "public_read": public_read,

        "public_write": public_write,
    }


# ==========================================================
# IAM
# ==========================================================

def map_iam_policy(
    policy_name: str,
    document: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Extract first IAM Action.

    Example

    Action:

        s3:*

    or

        ec2:DescribeInstances
    """

    action = ""

    statements = document.get("Statement", [])

    if not isinstance(statements, list):

        statements = [statements]

    for statement in statements:

        value = statement.get("Action")

        if value is None:
            continue

        if isinstance(value, list):

            action = value[0]

        else:

            action = value

        break

    return {

        "resource_id": policy_name,

        "resource_type": "iam_policy",

        "action": action,
    }


# ==========================================================
# Security Groups
# ==========================================================

def map_security_group(
    group: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Only the first CIDR is needed for Phase-1 rules.
    """

    cidr = ""

    permissions: List = group.get("IpPermissions", [])

    if permissions:

        ranges = permissions[0].get("IpRanges", [])

        if ranges:

            cidr = ranges[0].get("CidrIp", "")

    return {

        "resource_id": group["GroupId"],

        "resource_type": "security_group",

        "ingress": {

            "cidr": cidr
        }
    }


# ==========================================================
# Generic Dispatcher
# ==========================================================

RESOURCE_MAPPERS = {

    "s3_bucket": map_s3_bucket,

    "iam_policy": map_iam_policy,

    "security_group": map_security_group,
}


def map_resource(
    resource_type: str,
    *args,
    **kwargs,
):
    """
    Generic dispatcher.

    Example

    map_resource("s3_bucket", bucket_name, acl)
    """

    mapper = RESOURCE_MAPPERS.get(resource_type)

    if mapper is None:

        raise ValueError(
            f"No mapper found for {resource_type}"
        )

    return mapper(*args, **kwargs)