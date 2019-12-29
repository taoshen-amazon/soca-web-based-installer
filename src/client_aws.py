import sys

try:
    import boto3
except ImportError:
    print("boto3 extension is required. Run 'pip install boto3' and try again")
    sys.exit(1)


class CheckAWSConfiguration:
    def __init__(self, session, region="us-east-1"):
        if "profile" in session.keys():
            self.session = boto3.Session(profile_name=session["profile"],
                                         region_name=region)

        elif "access_key" in session.keys() and "secret_key" in session.keys():
            self.session = boto3.Session(aws_access_key_id=session["access_key"],
                                         aws_secret_access_key=session["secret_key"],
                                         region_name=region)

        else:
            self.session = boto3.Session(aws_access_key_id="INVALID",
                                         aws_secret_access_key="INVALID",
                                         region_name=region)

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

    def get_security_groups(self):
        try:
            ec2 = self.session.client('ec2')
            sgs = {}
            for sg in ec2.describe_security_groups()['SecurityGroups']:
                sgs[sg['GroupId']] = sg['GroupId'] + " (" + sg['GroupName'] + ")"

            return {'success': True,
                    'message': sgs}

        except Exception as err:
            return {'success': False,
                    'message': str(err)}

    def get_rules_for_security_group(self, sg_ids):
        try:
            ec2 = self.session.client('ec2')
            rules = {}
            for sg_id in sg_ids:
                for sg in ec2.describe_security_groups()['SecurityGroups']:
                    whitelist_rules = []
                    if sg['GroupId'] == sg_id:
                        if 'IpPermissions' in sg.keys():
                            for permission in sg['IpPermissions']:
                                if 'FromPort' in permission.keys():
                                    from_port = permission['FromPort']
                                    to_port = permission['ToPort']
                                else:
                                    # IpProtocol = -1 -> All Traffic
                                    from_port = 0
                                    to_port = 65535

                                whitelist_ip = []

                                if permission['IpRanges'].__len__() > 0:
                                    for r in permission['IpRanges']:
                                        if 'CidrIp' in r.keys():
                                            whitelist_ip.append(r['CidrIp'])

                                if permission['UserIdGroupPairs'].__len__() > 0:
                                    for g in permission['UserIdGroupPairs']:
                                        if 'GroupId' in g.keys():
                                            whitelist_ip.append(g['GroupId'])

                                whitelist_rules.append({'from_port': from_port,
                                                        'to_port': to_port,
                                                        'whitelist_ip': whitelist_ip,
                                                        'type': 'ingress'})

                                rules[sg_id] = whitelist_rules

                        if 'IpPermissionsEgress' in sg.keys():
                            for permission in sg['IpPermissionsEgress']:
                                if 'FromPort' in permission.keys():
                                    from_port = permission['FromPort']
                                    to_port = permission['ToPort']
                                else:
                                    # IpProtocol = -1 -> All Traffic
                                    from_port = 0
                                    to_port = 65535

                                whitelist_ip = []

                                if permission['IpRanges'].__len__() > 0:
                                    for r in permission['IpRanges']:
                                        if 'CidrIp' in r.keys():
                                            whitelist_ip.append(r['CidrIp'])

                                if permission['UserIdGroupPairs'].__len__() > 0:
                                    for g in permission['UserIdGroupPairs']:
                                        if 'GroupId' in g.keys():
                                            whitelist_ip.append(g['GroupId'])

                                whitelist_rules.append({'from_port': from_port,
                                                        'to_port': to_port,
                                                        'whitelist_ip': whitelist_ip,
                                                        'type': 'egress'})

                                rules[sg_id] = whitelist_rules

            return {'success': True,
                    'message': rules}

        except Exception as err:
            return {'success': False,
                    'message': str(err)}

    def get_subnets_az(self, subnet_id):
        try:
            ec2 = self.session.client('ec2')
            subnets = {}
            for subnet in subnet_id:
                for subnet in ec2.describe_subnets(Filters=[{'Name': 'subnet-id', 'Values': [subnet]}])['Subnets']:
                    subnets[subnet['SubnetId']] = subnet['AvailabilityZone']
            return {'success': True,
                    'message': subnets}

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

    def get_efs_security_groups(self, efs_ids):
        try:
            efs = self.session.client("efs")
            filesystems = {}
            for id in efs_ids:
                sgs = []
                for mount in efs.describe_mount_targets(FileSystemId=id.split(".")[0])["MountTargets"]:
                    for sg in efs.describe_mount_target_security_groups(MountTargetId=mount["MountTargetId"])['SecurityGroups']:
                        if sg not in sgs:
                            sgs.append(sg)

                filesystems[id] = sgs

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

    def get_regions(self):
        try:
            ec2 = self.session.client('ec2')
            regions = []
            for region in ec2.describe_regions()['Regions']:
                regions.append(region['RegionName'])
            return {'success': True,
                    'message': sorted(regions)}
        except Exception as err:
            return {'success': False,
                    'message': str(err)}

