import boto3
import json

# Specify the name of your Lambda function
lambda_function_name = 'your-lambda-function-name'

# Specify the SNS topic ARN
sns_topic_arn = 'your-sns-topic-arn'

# Specify the minimum and maximum number of instances
min_instances = 1
max_instances = 5

# Specify the scaling policy for increasing the instances
scale_out_policy = {
    "PolicyName": "ScaleOutPolicy",
    "ScalingAdjustment": 1,
    "AdjustmentType": "ChangeInCapacity"
}

# Specify the scaling policy for decreasing the instances
scale_in_policy = {
    "PolicyName": "ScaleInPolicy",
    "ScalingAdjustment": -1,
    "AdjustmentType": "ChangeInCapacity"
}

# Specify the threshold for scaling out, in terms of the average CPU utilization
scale_out_threshold = 80

# Specify the threshold for scaling in, in terms of the average CPU utilization
scale_in_threshold = 30

autoscaling = boto3.client('application-autoscaling')
lambda_client = boto3.client('lambda')

def set_scaling_policy(policy_name, scaling_adjustment, adjustment_type):
    response = autoscaling.put_scaling_policy(
        PolicyName=policy_name,
        ServiceNamespace='lambda',
        ResourceId=f"function:{lambda_function_name}",
        ScalableDimension='lambda:function:ProvisionedConcurrency',
        PolicyType='StepScaling',
        StepScalingPolicyConfiguration={
            'AdjustmentType': adjustment_type,
            'StepAdjustments': [
                {
                    'MetricIntervalLowerBound': 0,
                    'ScalingAdjustment': scaling_adjustment
                }
            ]
        }
    )

def enable_scaling_policies():
    set_scaling_policy(scale_out_policy['PolicyName'], scale_out_policy['ScalingAdjustment'], scale_out_policy['AdjustmentType'])
    set_scaling_policy(scale_in_policy['PolicyName'], scale_in_policy['ScalingAdjustment'], scale_in_policy['AdjustmentType'])

def get_message_data(event):
    message = event['Records'][0]['Sns']['Message']
    return json.loads(message)

def handle_scaling(event, context):
    message_data = get_message_data(event)
    average_cpu_utilization = message_data['Trigger']['Dimensions'][0]['Value']
    
    if average_cpu_utilization > scale_out_threshold:
        response = autoscaling.execute_policy(
            PolicyName=scale_out_policy['PolicyName'],
            ServiceNamespace='lambda',
            ResourceId=f"function:{lambda_function_name}"
        )
    elif average_cpu_utilization < scale_in_threshold:
        response = autoscaling.execute_policy(
            PolicyName=scale_in_policy['PolicyName'],
            ServiceNamespace='lambda',
            ResourceId=f"function:{lambda_function_name}"
        )

def lambda_handler(event, context):
    handle_scaling(event, context)
