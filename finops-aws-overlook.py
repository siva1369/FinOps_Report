import boto3
from botocore.exceptions import ClientError
from rich.console import Console
from rich.table import Table, Column
from rich import box

profiles = ['05', '02', '03', '04']
console = Console()

def get_active_services_summary(session):
    summary = {}

    # EC2
    try:
        ec2 = session.client('ec2')
        regions = [r['RegionName'] for r in ec2.describe_regions()['Regions']]
        running_ec2 = 0
        for region in regions:
            ec2_regional = session.client('ec2', region_name=region)
            instances = ec2_regional.describe_instances()
            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    if instance['State']['Name'] == 'running':
                        running_ec2 += 1
        if running_ec2 > 0:
            summary['EC2'] = f"{running_ec2} Running"
    except Exception as e:
        summary['EC2'] = f"Error: {e}"

    # S3
    try:
        s3 = session.client('s3')
        buckets = s3.list_buckets()['Buckets']
        if buckets:
            summary['S3'] = f"{len(buckets)} Buckets"
    except Exception as e:
        summary['S3'] = f"Error: {e}"

    # Lambda
    try:
        lambda_client = session.client('lambda')
        functions = lambda_client.list_functions()['Functions']
        if functions:
            summary['Lambda'] = f"{len(functions)} Functions"
    except Exception as e:
        summary['Lambda'] = f"Error: {e}"

    # IAM Users
    try:
        iam = session.client('iam')
        users = iam.list_users()['Users']
        if users:
            summary['IAM Users'] = f"{len(users)} Users"
    except Exception as e:
        summary['IAM Users'] = f"Error: {e}"

    # RDS
    try:
        rds = session.client('rds')
        instances = rds.describe_db_instances()['DBInstances']
        active_rds = [db for db in instances if db['DBInstanceStatus'] == 'available']
        if active_rds:
            summary['RDS'] = f"{len(active_rds)} Available"
    except Exception as e:
        summary['RDS'] = f"Error: {e}"

    # ECS Clusters with active services
    try:
        ecs = session.client('ecs')
        clusters = ecs.list_clusters()['clusterArns']
        active_clusters = 0
        for cluster_arn in clusters:
            services = ecs.list_services(cluster=cluster_arn)['serviceArns']
            if services:
                active_clusters += 1
        if active_clusters > 0:
            summary['ECS'] = f"{active_clusters} Clusters with Services"
    except Exception as e:
        summary['ECS'] = f"Error: {e}"

    # CloudWatch Alarms
    try:
        cw = session.client('cloudwatch')
        alarms = cw.describe_alarms()['MetricAlarms']
        if alarms:
            summary['CloudWatch Alarms'] = f"{len(alarms)} Alarms"
    except Exception as e:
        summary['CloudWatch Alarms'] = f"Error: {e}"

    return summary


# Rich Table Setup
table = Table(
    Column("AWS Profile", justify="center", style="bold magenta"),
    Column("Active Services", justify="left", style="cyan"),
    title="🛰️ AWS Account Resource Overview",
    box=box.SIMPLE_HEAVY,
    show_lines=True
)

for profile in profiles:
    console.log(f"Scanning profile: {profile}")
    try:
        session = boto3.Session(profile_name=profile)
        active_summary = get_active_services_summary(session)
        service_lines = [f"{k}: {v}" for k, v in active_summary.items()]
        if not service_lines:
            service_lines = ["No active resources found."]
        table.add_row(profile, "\n".join(service_lines))
    except ClientError as e:
        table.add_row(profile, f"Client error: {str(e)}")
    except Exception as e:
        table.add_row(profile, f"Unexpected error: {str(e)}")

console.print(table)
