import boto3
from rich.console import Console
from rich.table import Table, Column
from rich import box
from rich.live import Live

profiles = ['05', '02', '03', '04']
console = Console()

def get_ec2_summary(session):
    regions = ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2', 'ap-southeast-1', 'ap-south-1']
    summary = {'running': 0, 'stopped': 0}
    for region in regions:
        try:
            ec2 = session.client('ec2', region_name=region)
            response = ec2.describe_instances()
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    state = instance['State']['Name']
                    if state in summary:
                        summary[state] += 1
        except:
            continue
    return summary

def get_s3_summary(session):
    try:
        s3 = session.client('s3')
        response = s3.list_buckets()
        return len(response.get('Buckets', []))
    except:
        return 0

def get_iam_summary(session):
    try:
        iam = session.client('iam')
        users = iam.list_users().get('Users', [])
        roles = iam.list_roles().get('Roles', [])
        return {'users': len(users), 'roles': len(roles)}
    except:
        return {'users': 0, 'roles': 0}

def get_lambda_summary(session):
    regions = ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2', 'ap-southeast-1', 'ap-south-1']
    count = 0
    for region in regions:
        try:
            lambda_client = session.client('lambda', region_name=region)
            functions = lambda_client.list_functions().get('Functions', [])
            count += len(functions)
        except:
            continue
    return count

# Create table layout
table = Table(
    Column("AWS Profile", justify="center"),
    Column("EC2 Summary", justify="left"),
    Column("S3 Buckets", justify="center"),
    Column("IAM (Users/Roles)", justify="center"),
    Column("Lambda Functions", justify="center"),
    title="🔍 AWS Account Resource Summary",
    caption="Made by Sivaiah",
    box=box.DOUBLE,
    show_lines=True,
    style="cyan"
)

with Live(table, console=console, refresh_per_second=2):
    for profile in profiles:
        console.log(f"[green]Fetching data for profile: {profile}[/green]")
        try:
            session = boto3.Session(profile_name=profile)

            ec2 = get_ec2_summary(session)
            s3_count = get_s3_summary(session)
            iam = get_iam_summary(session)
            lambda_count = get_lambda_summary(session)

            table.add_row(
                f"[bold magenta]{profile}[/bold magenta]",
                f"Running: {ec2['running']}\nStopped: {ec2['stopped']}",
                f"{s3_count}",
                f"{iam['users']} / {iam['roles']}",
                f"{lambda_count}"
            )

            console.log(f"[blue]Finished profile: {profile}[/blue]")
        except Exception as e:
            console.log(f"[red]Error for profile {profile}: {e}[/red]")
