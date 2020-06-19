from flask import Flask, Response, request,  render_template
from twilio import twiml
from twilio.twiml.messaging_response import Body, Message, Redirect, MessagingResponse
import subprocess
app = Flask(__name__)
import boto3

ec2 = boto3.resource('ec2')

def run_process(a_cmd):
    the_command = "docker  %s" %a_cmd
    try:
        the_shell_cmd = subprocess.Popen(the_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        the_stdout, the_stderr = the_shell_cmd.communicate()
        the_return_code = the_shell_cmd.returncode
        if the_return_code == 0:
            return the_stdout
    except Exception as e:
        raise e



@app.route('/')

def check_app(): 
    WELCOME = "Welcome to the App"
    return render_template('index.html')

@app.route("/twilio", methods=["POST"])
def inbound_message():
    # Retrieve response from twilio
    print("request.form_body is", request.form.get("Body"))
    response = MessagingResponse()
    # Gets the inbound message for SMS messags only
    inbound_message = request.form.get("Body")
    # Parses the inbound messages to only contain command and arguements
    str_array = parse_message(inbound_message)


    if str_array[0] == ("hello"):
        response.message("""
            "Welcome to EC2 Viewer"
            1 - View all EC2 instances
            2 - View running EC2 instances
            3 - View stopped EC2 instances""")

    elif str_array[0] == "viewall":
        for instance in ec2.instances.all():
            msg=(instance.id, instance.instance_type, instance.state)
            response.message(str(msg))
    elif str_array[0] == "running":
            instanceses = ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
            for instance in instanceses:
                msg=(instance.id, instance.instance_type, instance.state)
                response.message(str(msg))
    elif str_array[0] == "stopped":
        instances = ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['stopped']}])
        for instance in instances:
            msg=(instance.id, instance.instance_type, instance.state)
            response.message(str(msg))


    return Response(str(response), mimetype="application/xml"), 200


def parse_message(message):
    str_array = message.split(' ')
    str_array[0] = str_array[0].lower()
    return str_array

def __help(message, response):
       response.message("Invalid Request")



if __name__ == '__main__':
    app.run(debug=True,host='127.0.0.1')
