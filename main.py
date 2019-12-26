import sys
import requests
try:
    from flask import Flask, render_template, request, redirect
except ImportError:
    print("Flask extension is required. Run 'pip install flask' and try again")
    sys.exit(1)

from src import get_awscli_credentials
import src.client_aws as client
app = Flask(__name__)



def validate_parameters(request, expected_parameters):
    param_value = {}
    for parameter in expected_parameters:
        if parameter not in request.args.keys():
            return False
        else:
            param_value[parameter] = request.args[parameter]

    return param_value


@app.route("/")
def index():
    return render_template("index.html",
                           step=0)


@app.route("/environment")
def environment():
    envs = get_awscli_credentials.get_config_file()
    return render_template("environment.html",
                           step=1,
                           envs=envs,
                           get_params=request.args)

@app.route("/region")
def region():
    if validate_parameters(request, ["env"]) is False:
        return redirect("/")
    regions = get_awscli_credentials.get_regions()
    return render_template("region.html",
                           step=2,
                           message=regions,
                           get_params=request.args)


@app.route("/vpc")
def vpc():
    if validate_parameters(request, ["region", "env"]) is False:
        return redirect("/")

    vpcs = client.CheckAWSConfiguration(request.args["env"], request.args["region"]).get_vpcs()
    return render_template("vpc.html",
                           success=vpcs["success"],
                           step=3,
                           message=vpcs["message"],
                           get_params=request.args)


@app.route("/private_subnets")
def private_subnets():
    if validate_parameters(request, ["region", "env", "vpc"]) is False:
        return redirect("/")

    subnets = client.CheckAWSConfiguration(request.args["env"], request.args["region"]).get_subnets(request.args["vpc"])
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
    if validate_parameters(request, ["region", "env", "vpc", "private_subnet_1", "private_subnet_2", "private_subnet_3"]) is False:
        return redirect("/")

    subnets = client.CheckAWSConfiguration(request.args["env"], request.args["region"]).get_subnets(request.args["vpc"])

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


@app.route("/efs_data")
def efs_data():
    if validate_parameters(request, ["region", "env", "vpc", "private_subnet_1", "private_subnet_2", "private_subnet_3",
                                     "public_subnet_1", "public_subnet_2", "public_subnet_3"]) is False:
        return redirect("/")
    filesystems = client.CheckAWSConfiguration(request.args["env"], request.args["region"]).get_efs()
    return render_template("efs_data.html",
                           step=6,
                           message=filesystems["message"],
                           success=filesystems["success"],
                           get_params=request.args)


@app.route("/efs_apps")
def efs_apps():
    if validate_parameters(request, ["region", "env", "vpc", "private_subnet_1", "private_subnet_2", "private_subnet_3",
                          "public_subnet_1", "public_subnet_2", "public_subnet_3", "efs_data"]) is False:
        return redirect("/")
    filesystems = client.CheckAWSConfiguration(request.args["env"], request.args["region"]).get_efs()
    filesystems["message"].pop(validate_parameters(request, ["efs_data"])["efs_data"])
    return render_template("efs_apps.html",
                           step=7,
                           message=filesystems["message"],
                           success=filesystems["success"],
                           get_params=request.args)


@app.route("/ssh")
def ssh():
    if validate_parameters(request, ["region", "env", "vpc", "private_subnet_1", "private_subnet_2", "private_subnet_3",
                          "public_subnet_1", "public_subnet_2", "public_subnet_3", "efs_data", "efs_apps"]) is False:
        return redirect("/")
    keys = client.CheckAWSConfiguration(request.args["env"], request.args["region"]).get_security_keys()
    return render_template("ssh.html",
                           step=8,
                           message=keys["message"],
                           success=keys["success"],
                           get_params=request.args)


@app.route("/s3_bucket")
def s3_bucket():
    if validate_parameters(request, ["region", "env", "vpc", "private_subnet_1", "private_subnet_2", "private_subnet_3",
                          "public_subnet_1", "public_subnet_2", "public_subnet_3", "efs_data", "efs_apps", "key"]) is False:
        return redirect("/")
    buckets = client.CheckAWSConfiguration(request.args["env"], request.args["region"]).get_s3_bucket()
    return render_template("s3_bucket.html",
                           step=9,
                           message=buckets["message"],
                           success=buckets["success"],
                           get_params=request.args)


@app.route("/s3_folder")
def s3_folder():
    if validate_parameters(request, ["region", "env", "vpc", "private_subnet_1", "private_subnet_2", "private_subnet_3",
                          "public_subnet_1", "public_subnet_2", "public_subnet_3", "efs_data", "efs_apps", "key", "s3_bucket"]) is False:
        return redirect("/")
    folders = client.CheckAWSConfiguration(request.args["env"], request.args["region"]).get_s3_folder(request.args["s3_bucket"])
    return render_template("s3_folder.html",
                           step=10,
                           message=folders["message"],
                           success=folders["success"],
                           get_params=request.args)

@app.route("/client_ip")
def client_ip():
    if validate_parameters(request, ["region", "env", "vpc", "private_subnet_1", "private_subnet_2", "private_subnet_3",
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

@app.route("/stack_name")
def stack_name():
    if validate_parameters(request, ["region", "env", "vpc", "private_subnet_1", "private_subnet_2", "private_subnet_3",
                          "public_subnet_1", "public_subnet_2", "public_subnet_3", "efs_data", "efs_apps", "key", "s3_bucket", "client_ip"]) is False:
        return redirect("/")
    return render_template("stack_name.html",
                           step=12,
                           get_params=request.args)

@app.route("/review")
def review():
    if validate_parameters(request, ["region", "env", "vpc", "private_subnet_1", "private_subnet_2", "private_subnet_3",
                          "public_subnet_1", "public_subnet_2", "public_subnet_3", "efs_data", "efs_apps", "key", "s3_bucket", "client_ip", "stack_name"]) is False:
        return redirect("/")
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
                         "&param_ClientIp=" + request.args["client_ip"]

    return render_template("review.html",
                           step=13,
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
