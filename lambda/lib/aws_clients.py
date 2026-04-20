import json
import boto3
from typing import Dict, Any, Tuple


class DynamoDBClient:
    """Wrapper for DynamoDB operations"""

    def __init__(self, region: str = None):
        self.dynamodb = boto3.resource("dynamodb", region_name=region)

    def get_table(self, table_name: str):
        """Get DynamoDB table resource"""
        return self.dynamodb.Table(table_name)

    def put_item(self, table_name: str, item: Dict[str, Any]) -> bool:
        """Put item in DynamoDB"""
        try:
            table = self.get_table(table_name)
            table.put_item(Item=item)
            return True
        except Exception as e:
            print(f"Error putting item in {table_name}: {str(e)}")
            raise

    def get_item(self, table_name: str, key: Dict[str, Any]) -> Dict[str, Any]:
        """Get item from DynamoDB"""
        try:
            table = self.get_table(table_name)
            response = table.get_item(Key=key)
            return response.get("Item", {})
        except Exception as e:
            print(f"Error getting item from {table_name}: {str(e)}")
            raise

    def update_item(
        self,
        table_name: str,
        key: Dict[str, Any],
        update_expression: str,
        expression_attribute_values: Dict = None,
        expression_attribute_names: Dict = None,
    ) -> Dict[str, Any]:
        """Update item in DynamoDB"""
        try:
            table = self.get_table(table_name)
            response = table.update_item(
                Key=key,
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values or {},
                ExpressionAttributeNames=expression_attribute_names or {},
                ReturnValues="ALL_NEW",
            )
            return response.get("Attributes", {})
        except Exception as e:
            print(f"Error updating item in {table_name}: {str(e)}")
            raise

    def query(
        self,
        table_name: str,
        key_condition_expression: str,
        expression_attribute_values: Dict = None,
        expression_attribute_names: Dict = None,
        index_name: str = None,
    ) -> list:
        """Query items from DynamoDB"""
        try:
            table = self.get_table(table_name)
            params = {
                "KeyConditionExpression": key_condition_expression,
                "ExpressionAttributeValues": expression_attribute_values or {},
            }
            if expression_attribute_names:
                params["ExpressionAttributeNames"] = expression_attribute_names
            if index_name:
                params["IndexName"] = index_name

            response = table.query(**params)
            return response.get("Items", [])
        except Exception as e:
            print(f"Error querying {table_name}: {str(e)}")
            raise

    def scan(
        self,
        table_name: str,
        filter_expression: str = None,
        expression_attribute_values: Dict = None,
        expression_attribute_names: Dict = None,
    ) -> list:
        """Scan items from DynamoDB"""
        try:
            table = self.get_table(table_name)
            params = {}
            if filter_expression:
                params["FilterExpression"] = filter_expression
                params["ExpressionAttributeValues"] = expression_attribute_values or {}
            if expression_attribute_names:
                params["ExpressionAttributeNames"] = expression_attribute_names

            response = table.scan(**params)
            return response.get("Items", [])
        except Exception as e:
            print(f"Error scanning {table_name}: {str(e)}")
            raise

    def conditional_put_item(
        self, table_name: str, item: Dict[str, Any], condition_expression: str
    ) -> Tuple[bool, str]:
        """Put item with condition (for preventing duplicates)"""
        try:
            table = self.get_table(table_name)
            table.put_item(Item=item, ConditionExpression=condition_expression)
            return True, "Item created successfully"
        except table.meta.client.exceptions.ConditionalCheckFailedException:
            return False, "Item already exists or condition not met"
        except Exception as e:
            print(f"Error in conditional put for {table_name}: {str(e)}")
            raise

    def delete_item(self, table_name: str, key: Dict[str, Any]) -> bool:
        """Delete item from DynamoDB"""
        try:
            table = self.get_table(table_name)
            table.delete_item(Key=key)
            return True
        except Exception as e:
            print(f"Error deleting item from {table_name}: {str(e)}")
            raise


class SNSClient:
    """Wrapper for SNS operations"""

    def __init__(self, region: str = None):
        self.sns = boto3.client("sns", region_name=region)

    def publish_sms(
        self, phone_number: str, message: str, topic_arn: str = None
    ) -> str:
        """Publish SMS to phone number"""
        try:
            if topic_arn:
                response = self.sns.publish(
                    TopicArn=topic_arn,
                    Message=message,
                    MessageAttributes={
                        "AWS.SNS.SMS.SenderID": {
                            "DataType": "String",
                            "StringValue": "VotingOTP",
                        },
                        "AWS.SNS.SMS.SMSType": {
                            "DataType": "String",
                            "StringValue": "Transactional",
                        },
                    },
                )
            else:
                response = self.sns.publish(
                    PhoneNumber=phone_number,
                    Message=message,
                    MessageAttributes={
                        "AWS.SNS.SMS.SenderID": {
                            "DataType": "String",
                            "StringValue": "VotingOTP",
                        },
                        "AWS.SNS.SMS.SMSType": {
                            "DataType": "String",
                            "StringValue": "Transactional",
                        },
                    },
                )
            return response["MessageId"]
        except Exception as e:
            print(f"Error publishing SMS to {phone_number}: {str(e)}")
            raise
