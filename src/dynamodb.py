import logging

log = logging.getLogger(__name__)

# Mock Data for testing
MOCK_DEVICES = [
    {
        "device_id": "FL-1023",
        "tank_level": 18,
        "sump_level": 12,
        "timestamp": "2026-06-08T10:30:00Z"
    },
    {
        "device_id": "FL-1024",
        "tank_level": 80,
        "sump_level": 45,
        "timestamp": "2026-06-08T10:30:00Z"
    },
    {
        "device_id": "FL-1025",
        "tank_level": 50,
        "sump_level": 5,
        "timestamp": "2026-06-08T10:30:00Z"
    }
]

def fetch_device_data() -> list:
    """
    Fetch device water level readings.
    For production, uncomment the boto3 block below to pull from DynamoDB.
    """
    # import boto3
    # try:
    #     table = boto3.resource("dynamodb").Table("device_data")
    #     return table.scan()["Items"]
    # except Exception as e:
    #     log.error(f"Failed to scan DynamoDB table: {e}")
    #     return []
    
    log.info('Using mock device data (DynamoDB not connected)')
    return MOCK_DEVICES
