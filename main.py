import sys
import requests
import ipaddress
import uuid
try:
    from flask import Flask, render_template, request, redirect, session
except ImportError:
    print("Flask extension is required. Run 'pip install flask' and try again")
    sys.exit(1)

from src import get_awscli_credentials
import src.client_aws as client
app = Flask(__name__)
app.config["SECRET_KEY"] = str(uuid.uuid4())



def validate_parameters(request, expected_parameters):
    param_value = {}
    for parameter in expected_parameters:
        if parameter not in request.args.keys():
            return False
        else:
            if parameter == "mode":
                if request.args[parameter] not in ["standard", "advanced"]:
                    return False
            param_value[parameter] = request.args[parameter]

    return param_value


@app.route("/")
def index():
    session.clear()
    return render_template("index.html",
                           step=0)

@app.route("/prerequisites")
def prerequisites():
    return render_template("prerequisites.html",
                           step=0,
                           get_params=request.args)

@app.route("/environment")
def environment():
    if validate_parameters(request, ["mode"]) is False:
        return redirect("/")

    envs = get_awscli_credentials.get_config_file()
    return render_template("environment.html",
                           step=1,
                           envs=envs,
                           get_params=request.args)


@app.route("/auth", methods=["POST"])
def auth():
    try:
        if "access_key" in request.form.keys() and "secret_key" in request.form.keys():
            session["access_key"] = request.form["access_key"]
            session["secret_key"] = request.form["secret_key"]

        elif "profile" in request.form.keys():
            session["profile"] = request.form["profile"]

        else:
            return redirect("/")

        return redirect("/region?mode=" + request.form["mode"])

    except:
        return redirect("/")


@app.route("/region")
def region():
    if validate_parameters(request, ["mode"]) is False:
        return redirect("/")

    regions = client.CheckAWSConfiguration(session).get_regions()
    return render_template("region.html",
                           step=2,
                           message=regions["message"],
                           success=regions["success"],
                           get_params=request.args)


@app.route("/vpc")
def vpc():
    if validate_parameters(request, ["mode", "region"]) is False:
        return redirect("/")

    vpcs = client.CheckAWSConfiguration(session, request.args["region"]).get_vpcs()
    return render_template("vpc.html",
                           success=vpcs["success"],
                           step=3,
                           message=vpcs["message"],
                           get_params=request.args)

@app.route("/vpc_cidr")
def vpc_cidr():
    if validate_parameters(request, ["region", "mode"]) is False:
        return redirect("/")

    return render_template("vpc_cidr.html",
                           step=3,
                           get_params=request.args)


@app.route("/private_subnets")
def private_subnets():
    if validate_parameters(request, ["mode", "region", "vpc"]) is False:
        return redirect("/")

    subnets = client.CheckAWSConfiguration(session, request.args["region"]).get_subnets(request.args["vpc"])
    if validate_parameters(request, ["private_subnet_1"]) is False:
        subnet_count = 1
    else:
        if validate_parameters(request, ["private_subnet_2"]) is False:
            subnet_count = 2
            subnets["message"].pop(validate_parameters(request, ["private_subnet_1"])["private_subnet_1"])
        else:
            if validate_parameters(request, ["private_subnet_3"]) is False:
                subnet_count = 3
                subnets["message"].pop(validate_parameters(request, ["private_subnet_1"])["private_subnet_1"])
                subnets["message"].pop(validate_parameters(request, ["private_subnet_2"])["private_subnet_2"])

    return render_template("private_subnets.html",
                           step=4,
                           id=subnet_count,
                           message=subnets["message"],
                           success=subnets["success"],
                           get_params=request.args)


@app.route("/public_subnets")
def public_subnets():
    if validate_parameters(request, ["mode", "region", "vpc", "private_subnet_1", "private_subnet_2", "private_subnet_3"]) is False:
        return redirect("/")

    subnets = client.CheckAWSConfiguration(session, request.args["region"]).get_subnets(request.args["vpc"])

    if validate_parameters(request, ["public_subnet_1"]) is False:
        subnet_count = 1
        subnets["message"].pop(validate_parameters(request, ["private_subnet_1"])["private_subnet_1"])
        subnets["message"].pop(validate_parameters(request, ["private_subnet_2"])["private_subnet_2"])
        subnets["message"].pop(validate_parameters(request, ["private_subnet_3"])["private_subnet_3"])
    else:
        if validate_parameters(request, ["public_subnet_2"]) is False:
            subnet_count = 2
            subnets["message"].pop(validate_parameters(request, ["public_subnet_1"])["public_subnet_1"])
            subnets["message"].pop(validate_parameters(request, ["private_subnet_1"])["private_subnet_1"])
            subnets["message"].pop(validate_parameters(request, ["private_subnet_2"])["private_subnet_2"])
            subnets["message"].pop(validate_parameters(request, ["private_subnet_3"])["private_subnet_3"])
        else:
            if validate_parameters(request,["public_subnet_3"]) is False:
                subnet_count = 3
                subnets["message"].pop(validate_parameters(request, ["public_subnet_1"])["public_subnet_1"])
                subnets["message"].pop(validate_parameters(request, ["public_subnet_2"])["public_subnet_2"])
                subnets["message"].pop(validate_parameters(request, ["private_subnet_1"])["private_subnet_1"])
                subnets["message"].pop(validate_parameters(request, ["private_subnet_2"])["private_subnet_2"])
                subnets["message"].pop(validate_parameters(request, ["private_subnet_3"])["private_subnet_3"])

    return render_template("public_subnets.html",
                           step=5,
                           id=subnet_count,
                           message=subnets["message"],
                           success=subnets["success"],
                           get_params=request.args)


@app.route("/subnet_verif")
def subnet_verif():
    if validate_parameters(request, ["mode", "region", "vpc", "private_subnet_1", "private_subnet_2", "private_subnet_3",
                                     "public_subnet_1", "public_subnet_2", "public_subnet_3"]) is False:
        return redirect("/")

    messages = {}
    get_private_subnets_az = client.CheckAWSConfiguration(session, request.args["region"]).get_subnets_az([request.args["private_subnet_1"], request.args["private_subnet_2"],request.args["private_subnet_3"]])
    get_public_subnets_az = client.CheckAWSConfiguration(session, request.args["region"]).get_subnets_az([request.args["public_subnet_1"], request.args["public_subnet_2"],request.args["public_subnet_3"]])
    errors = {'PUBLIC_SUBNETS_DUPLICATE': {"status": False, "error": "You must use different Availability Zones for your public subnets.", "resolution": "Make sure your 3 public subnets use different availability zones "},
              'PRIVATE_SUBNETS_DUPLICATE': {"status": False, "error": "You must use different Availability Zones for your private subnets.", "resolution": "Make sure your 3 private subnets use different availability zones "}}

    if len(get_public_subnets_az['message'].values()) == len(set(get_public_subnets_az['message'].values())):
        errors["PUBLIC_SUBNETS_DUPLICATE"]["status"] = True

    if len(get_private_subnets_az['message'].values()) == len(set(get_private_subnets_az['message'].values())):
        errors["PRIVATE_SUBNETS_DUPLICATE"]["status"] = True

    for k, v in errors.items():
        if v["status"] is False:
            messages[v["error"]] = v["resolution"]

    get_parameters_reset_subnet = []
    get_parameters = []
    for param, value in request.args.items():
        get_parameters.append(param + '=' + value)
        if param not in ["private_subnet_1", "private_subnet_2", "private_subnet_3",
                         "public_subnet_1", "public_subnet_2", "public_subnet_3"]:
            get_parameters_reset_subnet.append(param + '=' + value)


    if messages.__len__() == 0:
        return redirect("/efs_data?" + "&".join(get_parameters))
    else:
        go_back_button_href = "/private_subnets?" + "&".join(get_parameters_reset_subnet)
        return render_template("subnet_verif.html",
                            step=5,
                            go_back_button_href=go_back_button_href,
                            messages=messages,
                            get_public_subnets_az=get_public_subnets_az['message'],
                            get_private_subnets_az=get_private_subnets_az['message'],
                            get_params=request.args)





@app.route("/efs_data")
def efs_data():
    if validate_parameters(request, ["mode", "region", "vpc", "private_subnet_1", "private_subnet_2", "private_subnet_3",
                                     "public_subnet_1", "public_subnet_2", "public_subnet_3"]) is False:
        return redirect("/")
    filesystems = client.CheckAWSConfiguration(session, request.args["region"]).get_efs()
    return render_template("efs_data.html",
                           step=6,
                           message=filesystems["message"],
                           success=filesystems["success"],
                           get_params=request.args)


@app.route("/efs_apps")
def efs_apps():
    if validate_parameters(request, ["mode", "region", "vpc", "private_subnet_1", "private_subnet_2", "private_subnet_3",
                          "public_subnet_1", "public_subnet_2", "public_subnet_3", "efs_data"]) is False:
        return redirect("/")
    filesystems = client.CheckAWSConfiguration(session, request.args["region"]).get_efs()
    filesystems["message"].pop(validate_parameters(request, ["efs_data"])["efs_data"])
    return render_template("efs_apps.html",
                           step=7,
                           message=filesystems["message"],
                           success=filesystems["success"],
                           get_params=request.args)


@app.route("/ssh")
def ssh():
    if validate_parameters(request, ["mode"]) is False:
        return redirect("/")
    else:
        if request.args["mode"] == "standard":
            if validate_parameters(request, ["region", "vpc_cidr"]) is False:
                return redirect("/")
        else:
            if validate_parameters(request, ["region", "vpc", "private_subnet_1", "private_subnet_2", "private_subnet_3",
                                                 "public_subnet_1", "public_subnet_2", "public_subnet_3", "efs_data", "efs_apps"]) is False:
                return redirect("/")

    keys = client.CheckAWSConfiguration(session, request.args["region"]).get_security_keys()
    return render_template("ssh.html",
                           step=8,
                           message=keys["message"],
                           success=keys["success"],
                           get_params=request.args)


@app.route("/s3_bucket")
def s3_bucket():
    if validate_parameters(request, ["mode"]) is False:
        return redirect("/")
    else:
        if request.args["mode"] == "standard":
            if validate_parameters(request, ["region", "vpc_cidr", "key"]) is False:
                return redirect("/")
        else:
            if validate_parameters(request, ["mode", "region", "vpc", "private_subnet_1", "private_subnet_2", "private_subnet_3",
                          "public_subnet_1", "public_subnet_2", "public_subnet_3", "efs_data", "efs_apps", "key"]) is False:
                return redirect("/")

    buckets = client.CheckAWSConfiguration(session, request.args["region"]).get_s3_bucket()
    return render_template("s3_bucket.html",
                           step=9,
                           message=buckets["message"],
                           success=buckets["success"],
                           get_params=request.args)


@app.route("/s3_folder")
def s3_folder():
    if validate_parameters(request, ["mode"]) is False:
        return redirect("/")
    else:
        if request.args["mode"] == "standard":
            if validate_parameters(request, ["region", "vpc_cidr", "key","s3_bucket"]) is False:
                return redirect("/")
        else:
            if validate_parameters(request, ["mode", "region", "vpc", "private_subnet_1", "private_subnet_2", "private_subnet_3",
                          "public_subnet_1", "public_subnet_2", "public_subnet_3", "efs_data", "efs_apps", "key", "s3_bucket"]) is False:
                return redirect("/")

    folders = client.CheckAWSConfiguration(session, request.args["region"]).get_s3_folder(request.args["s3_bucket"])
    return render_template("s3_folder.html",
                           step=10,
                           message=folders["message"],
                           success=folders["success"],
                           get_params=request.args)

@app.route("/client_ip")
def client_ip():
    if validate_parameters(request, ["mode"]) is False:
        return redirect("/")
    else:
        if request.args["mode"] == "standard":
            if validate_parameters(request, ["region", "vpc_cidr", "key","s3_bucket", "s3_folder"]) is False:
                return redirect("/")
        else:
            if validate_parameters(request, ["mode", "region", "vpc", "private_subnet_1", "private_subnet_2", "private_subnet_3",
                                  "public_subnet_1", "public_subnet_2", "public_subnet_3", "efs_data", "efs_apps", "key", "s3_bucket", "s3_folder"]) is False:
                return redirect("/")
    check_ip_endpoint = "https://ifconfig.co/ip"
    req = requests.get(check_ip_endpoint)
    ip = {}
    if req.status_code == 200:
        ip["success"] = True
        ip["message"] = str(req.text).rstrip() + "/32"
    else:
        ip["success"] = False
        ip["message"] = "0.0.0.0/0"

    return render_template("client_ip.html",
                           step=11,
                           message=ip["message"],
                           success=ip["success"],
                           get_params=request.args)

@app.route("/security_groups")
def security_groups():
    if validate_parameters(request, ["region", "vpc", "private_subnet_1", "private_subnet_2", "private_subnet_3",
                          "public_subnet_1", "public_subnet_2", "public_subnet_3", "efs_data", "efs_apps", "key", "s3_bucket", "client_ip"]) is False:
        return redirect("/")

    sg = client.CheckAWSConfiguration(session, request.args["region"]).get_security_groups()

    return render_template("security_groups.html",
                           step=12,
                           message=sg["message"],
                           success=sg["success"],
                           get_params=request.args)


@app.route("/sg_verif")
def sg_verif():
    if validate_parameters(request, ["region", "vpc", "private_subnet_1", "private_subnet_2", "private_subnet_3",
                          "public_subnet_1", "public_subnet_2", "public_subnet_3", "efs_data", "efs_apps", "key", "s3_bucket", "client_ip", "sg_scheduler", "sg_compute"]) is False:
        return redirect("/")

    get_rules = client.CheckAWSConfiguration(session, request.args["region"]).get_rules_for_security_group([request.args['sg_scheduler'], request.args['sg_compute']])
    get_rules_efs = client.CheckAWSConfiguration(session, request.args["region"]).get_efs_security_groups([request.args['efs_apps'], request.args['efs_data']])
    if get_rules_efs["success"] is False:
        return render_template("sg_verif.html",
                               step=12,
                               success=get_rules_efs["success"],
                               message=get_rules_efs["message"],
                               get_params=request.args)

    rules_scheduler = get_rules['message'][request.args['sg_scheduler']]
    rules_compute = get_rules['message'][request.args['sg_compute']]


    errors = {"SCHEDULER_SG_IN_COMPUTE":  {"status": False, "error": "Scheduler SG must be authorized for all ports (All TCP) in Compute SG", "resolution": "Add new rule that allow TCP ports '0-65535' for " + request.args['sg_compute']},
              "COMPUTE_SG_IN_SCHEDULER":  {"status": False, "error": "Compute SG must be authorized for all ports (All TCP) in Scheduler SG", "resolution": "Add a new rule that allow TCP ports '0-65535' for " + request.args['sg_scheduler']},
              "CLIENT_IP_HTTPS_IN_SCHEDULER": {"status": False, "error": "Client IP must be allowed for port 443 (80 optional) in Scheduler SG", "resolution": "Add two rules on " + request.args['sg_scheduler'] + " for TCP/80 and TCP/443 for " + request.args['client_ip']},
              "CLIENT_IP_SSH_IN_SCHEDULER": {"status": False,"error": "Client IP must be allowed for port 22 (SSH) in Scheduler SG","resolution": "Add two rules on " + request.args['sg_scheduler'] + " for TCP/22 for " + request.args['client_ip']},

              "SCHEDULER_SG_EQUAL_COMPUTE":  {"status": False, "error": "Scheduler SG and Compute SG must be different", "resolution": "You must choose two different security groups"},
              "COMPUTE_SG_EGRESS_EFA": {"status": False, "error": "Compute SG must reference egress traffic to itself for EFA", "resolution": "Add a new (EGRESS) rule on " + request.args['sg_compute'] + " + that allow TCP ports '0-65535' for " + request.args['sg_compute'] +". Make sure you configure EGRESS rule and not INGRESS"},
              "EFS_APP_SG": {"status": False, "error": "SG assigned to EFS App " + request.args["efs_apps"] + " must allow Scheduler SG and Compute SG", "resolution": "Add " + request.args['sg_compute'] + " and " + request.args['sg_scheduler'] + " on your EFS Apps " + request.args["efs_apps"]},
              "EFS_DATA_SG": {"status": False, "error": "SG assigned to EFS App " + request.args["efs_data"] + " must allow Scheduler SG and Compute SG","resolution": "Add " + request.args['sg_compute'] + " and " + request.args['sg_scheduler'] + " on your EFS Data " + request.args["efs_data"]},
    }

    messages = {}
    for rules in rules_scheduler:
        if rules["from_port"] == 0 and rules["to_port"] == 65535:
            for rule in rules["whitelist_ip"]:
                if request.args['sg_compute'] in rule:
                    errors["COMPUTE_SG_IN_SCHEDULER"]["status"] = True

        if rules["from_port"] == 443 or rules["from_port"] == 22:
            for rule in rules["whitelist_ip"]:
                client_ip_netmask = request.args['client_ip'].split('/')[1]
                if client_ip_netmask == '32':
                    if ipaddress.IPv4Address(request.args['client_ip'].split('/')[0]) in ipaddress.IPv4Network(rule):
                        if rules["from_port"] == 443:
                            errors["CLIENT_IP_HTTPS_IN_SCHEDULER"]["status"] = True
                        if rules["from_port"] == 22:
                            errors["CLIENT_IP_SSH_IN_SCHEDULER"]["status"] = True
                else:
                    if request.args['client_ip'] in rule:
                        if rules["from_port"] == 443:
                            errors["CLIENT_IP_HTTPS_IN_SCHEDULER"]["status"] = True
                        if rules["from_port"] == 22:
                            errors["CLIENT_IP_SSH_IN_SCHEDULER"]["status"] = True

    for rules in rules_compute:
        if rules["from_port"] == 0 and rules["to_port"] == 65535:
            for rule in rules["whitelist_ip"]:
                if request.args['sg_scheduler'] in rule:
                    errors["SCHEDULER_SG_IN_COMPUTE"]["status"] = True

                if rules["type"] == "egress":
                    if request.args["sg_compute"] in rule:
                        errors["COMPUTE_SG_EGRESS_EFA"]["status"] = True


    if request.args['sg_scheduler'] in get_rules_efs['message'][request.args['efs_apps']] and request.args['sg_compute'] in get_rules_efs['message'][request.args['efs_apps']]:
        errors["EFS_APP_SG"]["status"] = True

    if request.args['sg_scheduler'] in get_rules_efs['message'][request.args['efs_data']] and request.args['sg_compute'] in get_rules_efs['message'][request.args['efs_data']]:
        errors["EFS_DATA_SG"]["status"] = True

    if request.args["sg_scheduler"] != request.args["sg_compute"]:
        errors["SCHEDULER_SG_EQUAL_COMPUTE"]["status"] = True

    for k, v in errors.items():
        if v["status"] is False:
            messages[v["error"]] = v["resolution"]

    get_parameters = []
    for param, value in request.args.items():
        get_parameters.append(param + '=' + value)

    if messages.__len__() == 0:
        return redirect("/image?" + "&".join(get_parameters))
    else:
        return render_template("sg_verif.html",
                               step=12,
                               messages=messages,
                               rules_scheduler=rules_scheduler,
                               rules_compute=rules_compute,
                               get_params=request.args)

@app.route("/image")
def image():
    if validate_parameters(request, ["mode"]) is False:
        return redirect("/")
    else:
        if request.args["mode"] == "standard":
            if validate_parameters(request, ["region", "vpc_cidr", "key", "s3_bucket", "s3_folder"]) is False:
                return redirect("/")
        else:
            if validate_parameters(request, ["region", "vpc", "private_subnet_1", "private_subnet_2", "private_subnet_3",
                          "public_subnet_1", "public_subnet_2", "public_subnet_3", "efs_data", "efs_apps", "key", "s3_bucket", "client_ip"]) is False:
                return redirect("/")

    return render_template("images.html",
                           step=13,
                           get_params=request.args)
@app.route("/stack_name")
def stack_name():
    if validate_parameters(request, ["mode"]) is False:
        return redirect("/")
    else:
        if request.args["mode"] == "standard":
            if validate_parameters(request, ["region", "vpc_cidr", "key","s3_bucket", "s3_folder", "base_os", "instance_ami"]) is False:
                return redirect("/")
        else:
            if validate_parameters(request, ["region", "vpc", "private_subnet_1", "private_subnet_2", "private_subnet_3",
                                  "public_subnet_1", "public_subnet_2", "public_subnet_3", "efs_data", "efs_apps", "key", "s3_bucket", "client_ip", "base_os", "instance_ami"]) is False:
                return redirect("/")
    return render_template("stack_name.html",
                           step=14,
                           get_params=request.args)

@app.route("/review")
def review():
    if validate_parameters(request, ["mode"]) is False:
        return redirect("/")
    else:
        if request.args["mode"] == "standard":
            if validate_parameters(request, ["region", "vpc_cidr", "key","s3_bucket", "s3_folder", "base_os", "instance_ami", "stack_name"]) is False:
                return redirect("/")
        else:
            if validate_parameters(request, ["region", "vpc", "private_subnet_1", "private_subnet_2", "private_subnet_3",
                                  "public_subnet_1", "public_subnet_2", "public_subnet_3", "efs_data", "efs_apps", "key", "s3_bucket", "client_ip",  "base_os", "instance_ami", "stack_name"]) is False:
                return redirect("/")


    if request.args["mode"] == "advanced":
        cloudformation_url = "https://console.aws.amazon.com/cloudformation/home?" \
                             "region=" + request.args["region"] + \
                             "#/stacks/create/review?" + \
                             "stackName="+ request.args["stack_name"] + \
                             "&templateURL=https://s3.amazonaws.com/" + request.args["s3_bucket"] + \
                             "/" + request.args["s3_folder"] + \
                             "/install-with-existing-resources.template" + \
                             "&param_VpcId=" + request.args["vpc"] + \
                             "&param_PrivateSubnet1=" + request.args["private_subnet_1"] + \
                             "&param_PrivateSubnet2=" + request.args["private_subnet_2"] + \
                             "&param_PrivateSubnet3=" + request.args["private_subnet_3"] + \
                             "&param_PublicSubnet1=" + request.args["public_subnet_1"] + \
                             "&param_PublicSubnet2=" + request.args["public_subnet_2"] + \
                             "&param_PublicSubnet3=" + request.args["public_subnet_3"] + \
                             "&param_EFSDataDns=" + request.args["efs_data"] + \
                             "&param_EFSAppsDns=" + request.args["efs_apps"] + \
                             "&param_SSHKeyPair=" + request.args["key"] + \
                             "&param_S3InstallBucket=" + request.args["s3_bucket"] + \
                             "&param_S3InstallFolder=" + request.args["s3_folder"] + \
                             "&param_ClientIp=" + request.args["client_ip"] + \
                             "&param_SecurityGroupIdScheduler=" + request.args["sg_scheduler"] + \
                             "&param_SecurityGroupIdCompute=" + request.args["sg_compute"] + \
                             "&param_BaseOS=" + request.args["base_os"] + \
                             "&param_CustomAMI=" + request.args["instance_ami"]

    if request.args["mode"] == "standard":
        cloudformation_url = "https://console.aws.amazon.com/cloudformation/home?" \
                             "region=" + request.args["region"] + \
                             "#/stacks/create/review?" + \
                             "stackName=" + request.args["stack_name"] + \
                             "&templateURL=https://s3.amazonaws.com/" + request.args["s3_bucket"] + \
                             "/" + request.args["s3_folder"] + \
                             "/scale-out-computing-on-aws.template" + \
                             "&param_VpcCidr=" + request.args["vpc_cidr"] + \
                             "&param_S3InstallBucket=" + request.args["s3_bucket"] + \
                             "&param_S3InstallFolder=" + request.args["s3_folder"] + \
                             "&param_ClientIp=" + request.args["client_ip"] + \
                             "&param_BaseOS=" + request.args["base_os"] + \
                             "&param_SSHKeyPair=" + request.args["key"] + \
                             "&param_CustomAMI=" + request.args["instance_ami"]




    return render_template("review.html",
                           step=15,
                           cloudformation_url=cloudformation_url,
                           parameters=request.args)


if __name__ == "__main__":
    host = "127.0.0.1"
    port = 5000
    debug = True
    print()
    print("=============================================")
    print("Access the installer using http://"+host+":"+str(port))
    print("=============================================")
    print()
    app.run(host=host, port=port, debug=debug)
