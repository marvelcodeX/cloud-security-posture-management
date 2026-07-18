"""
Unit tests for Phase-4 Cloud Connector.

Member-1

Tests

1. Resource Mapper
2. Normalizer
3. Cloud Collector
4. Contract A
"""

from unittest.mock import MagicMock, patch

from src.cloud.collector import (
    CloudCollector,
    collect_cloud_resources,
)

from src.cloud.normalizer import (
    normalize_resource,
)


# ==========================================================
# S3
# ==========================================================

def test_normalize_s3_bucket():

    acl = {

        "Grants": [

            {

                "Permission": "READ",

                "Grantee": {

                    "URI": "http://acs.amazonaws.com/groups/global/AllUsers"

                }

            }

        ]

    }

    resource = normalize_resource(

        "s3_bucket",

        "demo-bucket",

        acl,

    )

    assert resource["resource_id"] == "demo-bucket"

    assert resource["resource_type"] == "s3_bucket"

    assert resource["public_read"] is True

    assert resource["public_write"] is False


# ==========================================================
# IAM
# ==========================================================

def test_normalize_iam_policy():

    document = {

        "Statement": [

            {

                "Action": "s3:*"

            }

        ]

    }

    resource = normalize_resource(

        "iam_policy",

        "AdminPolicy",

        document,

    )

    assert resource["resource_type"] == "iam_policy"

    assert resource["action"] == "s3:*"


# ==========================================================
# Security Group
# ==========================================================

def test_normalize_security_group():

    group = {

        "GroupId": "sg-001",

        "IpPermissions": [

            {

                "IpRanges": [

                    {

                        "CidrIp": "0.0.0.0/0"

                    }

                ]

            }

        ]

    }

    resource = normalize_resource(

        "security_group",

        group,

    )

    assert resource["resource_type"] == "security_group"

    assert resource["ingress"]["cidr"] == "0.0.0.0/0"


# ==========================================================
# Collector
# ==========================================================

@patch("src.cloud.collector.get_ec2_client")
@patch("src.cloud.collector.get_iam_client")
@patch("src.cloud.collector.get_s3_client")
def test_collector_initialization(

    mock_s3,

    mock_iam,

    mock_ec2,

):

    CloudCollector()

    mock_s3.assert_called_once()

    mock_iam.assert_called_once()

    mock_ec2.assert_called_once()


# ==========================================================
# Contract A
# ==========================================================

@patch.object(

    CloudCollector,

    "collect",

)

def test_collect_cloud_resources(

    mock_collect,

):

    expected = [

        {

            "resource_id": "bucket-1",

            "resource_type": "s3_bucket",

            "public_read": False,

            "public_write": False,

        }

    ]

    mock_collect.return_value = expected

    resources = collect_cloud_resources()

    assert resources == expected

    mock_collect.assert_called_once()


# ==========================================================
# Empty Collection
# ==========================================================

@patch.object(

    CloudCollector,

    "collect_s3_resources",

)

@patch.object(

    CloudCollector,

    "collect_iam_resources",

)

@patch.object(

    CloudCollector,

    "collect_security_groups",

)

def test_empty_collection(

    mock_sg,

    mock_iam,

    mock_s3,

):

    mock_s3.return_value = []

    mock_iam.return_value = []

    mock_sg.return_value = []

    collector = CloudCollector()

    resources = collector.collect()

    assert resources == []


# ==========================================================
# Multiple Resources
# ==========================================================

@patch.object(

    CloudCollector,

    "collect_s3_resources",

)

@patch.object(

    CloudCollector,

    "collect_iam_resources",

)

@patch.object(

    CloudCollector,

    "collect_security_groups",

)

def test_multiple_resources(

    mock_sg,

    mock_iam,

    mock_s3,

):

    mock_s3.return_value = [

        {

            "resource_id": "bucket",

            "resource_type": "s3_bucket",

            "public_read": False,

            "public_write": False,

        }

    ]

    mock_iam.return_value = [

        {

            "resource_id": "policy",

            "resource_type": "iam_policy",

            "action": "s3:*",

        }

    ]

    mock_sg.return_value = [

        {

            "resource_id": "sg-1",

            "resource_type": "security_group",

            "ingress": {

                "cidr": "0.0.0.0/0"

            }

        }

    ]

    collector = CloudCollector()

    resources = collector.collect()

    assert len(resources) == 3

    assert resources[0]["resource_type"] == "s3_bucket"

    assert resources[1]["resource_type"] == "iam_policy"

    assert resources[2]["resource_type"] == "security_group"