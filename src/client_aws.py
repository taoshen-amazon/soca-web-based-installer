import sys
try:
    import boto3
except ImportError:
    print("boto3 extension is required. Run 'pip install boto3' and try again")
    sys.exit(1)


class CheckAWSConfiguration:
    def __init__(self, profile, region):
        self.profile = profile
        self.region = region
        self.session = boto3.Session(profile_name=self.profile,
                                     region_name=self.region)

    def get_vpcs(self):
        try:
            ec2 = self.session.client('ec2')
            vpcs = {}
            for vpc in ec2.describe_vpcs()['Vpcs']:
                vpcs[vpc['VpcId']] = vpc['VpcId'] + ' (' + vpc['CidrBlock'] +')'

            return {'success': True,
                    'message': vpcs}

        except Exception as err:
            return {'success': False,
                    'message': str(err)}

    def get_subnets(self, vpc_id):
        try:
            ec2 = self.session.client('ec2')
            subnets = {}
            for subnet in ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['Subnets']:
                subnets[subnet['SubnetId']] = subnet['SubnetId'] + ' ('+subnet['AvailabilityZone']+')' + ': '+subnet['CidrBlock']

            return {'success': True,
                    'message': subnets}

        except Exception as err:
            return {'success': False,
                    'message': str(err)}


    def get_security_keys(self):
        try:
            ec2 = self.session.client('ec2')
            keys = []
            for key in ec2.describe_key_pairs()['KeyPairs']:
                keys.append(key['KeyName'])

            return {'success': True,
                'message': keys}

        except Exception as err:
            return {'success': False,
                    'message': str(err)}

    def get_efs(self):
        try:
            efs = self.session.client("efs")
            filesystems = {}
            for filesystem in efs.describe_file_systems()['FileSystems']:
                filesystems[filesystem['FileSystemId'] + ".efs." + self.region + ".amazonaws.com" ] = filesystem['Name']
            return {"success": True,
                    "message": filesystems}

        except Exception as err:
            return {'success': False,
                    'message': str(err)}


    def get_s3_bucket(self):
        try:
            s3 = self.session.client("s3")
            buckets = []
            for bucket in s3.list_buckets()['Buckets']:
                buckets.append(bucket['Name'])
            return {'success': True,
                    'message': buckets}

        except Exception as err:
            return {'success': False,
                    'message': str(err)}


    def get_s3_folder(self, bucket_name):
        try:
            s3 = self.session.resource('s3')
            folders = []
            bucket = s3.Bucket(bucket_name)
            result = bucket.meta.client.list_objects(Bucket=bucket.name,
                                                     Delimiter='/')

            results = result.get('CommonPrefixes')
            if results is not None:
                for o in result.get('CommonPrefixes'):
                    folders.append(o.get('Prefix').replace('/',''))

            return {'success': True,
                    'message': folders}

        except Exception as err:
            return {'success': False,
                'message': str(err)}

