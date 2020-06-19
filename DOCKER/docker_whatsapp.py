from flask import Flask, Response, request,  render_template
from twilio import twiml
import docker
from twilio.twiml.messaging_response import Body, Message, Redirect, MessagingResponse
import subprocess
app = Flask(__name__)

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

    # Starts the Docker Client
    client = docker.from_env()

    if len(str_array) == 1 and str_array[0]!= 'ps' and str_array[0]!= 'hello':
         __help(str_array[0], response)

    # Conditions of inbound messages
    else:
         if str_array[0] == "hello":
             response.message("""'*****WELCOME***** \n'
'Manage your CONTAINERS by whatsapping docker commands \n'
'You Can : \n'
'-> RUN A CONTAINER INSTANCE\n'
'-> LIST CONTAINERS \n'
'-> STOP A CONTAINER INSTANCE \n'
'-> REMOVE A CONTAINER INSTANCE'""")
            # response.message("Manage your CONTAINERS by whatsapping docker commands")
            # response.message("You can: " \n
            #                  "Run, List, Stop and Delete your containers")

         elif str_array[0] == "run":
             print("string array is", str_array)
             # Run command, checks for detach mode, and name flag
             if "-d" in str_array:
                 idx = len(str_array) - 1
                 if "--name" in str_array:
                     name_idx = str_array.index("--name") + 1
                     try:
                         response.message(str(client.containers.run(str_array[idx], detach=True, name=str_array[name_idx])))
                     except:
                         response.message("Already being used, name is - " + name)
                 else:
                     response.message(str(client.containers.run(str_array[idx], detach=True)))
             else:
                 name_idx = ""
                 if "--name" in str_array:
                     name_idx = str_array.index("--name")
                     name_str = str_array[name_idx + 1]
                     del str_array[name_idx: name_idx + 2]
                 command_str = str_array[:]
                 del command_str[0:2]
                 command = " ".join(command_str)
                 if name_idx != "":
                     try:
                         response.message(str(client.containers.run(str_array[1], command, name=name_str, detach=True)))
                     except:
                         response.message("This name is already used. Pick something else!!")
                 else:
                     response.message(str(client.containers.run(str_array[1], command, detach=True)))
         elif str_array[0] == "ps":
             # PS command to list all containers, -a to list all stopped, -l to lastest container, -n to number
             if len(str_array) > 1:
                 if str_array[1] == "-a":
                     msg = run_process('ps -a --format "table {{.ID}}\t{{.Names}}"')

                     # msg = client.containers.list(all=True)
                 elif str_array[1] == "-l":
                     msg = client.containers.list(limit=1)
                 elif "-n" in str_array[1]:
                     number = str_array[1].split('=')
                     msg = client.containers.list(limit=int(number[1]))
                 else:
                     msg = "This flag is not available ."
                 response.message(str(msg))
             else:
                 msg = run_process('ps  --format "table {{.ID}}\t{{.Names}}"')
                 response.message(str(msg))
                 #response.message(str(client.containers.list()))
         elif str_array[0] == "create":
             # create the container but do not run it
             try:
                 if len(str_array) == 1:
                     response.message(str(client.containers.create(str_array[1])))
                 else:
                     command_str = str_array[:]
                     del command_str[0:2]
                     command = " ".join(command_str)
                     response.message(str(client.containers.create(str_array[1], command)))
             except:
                 response.message("Found the container is not.  Yes, hmmm.")
         elif str_array[0] == "rm":
             # rm a container given ID or Name
             response.message("Removing the container...  Yes, hmmm.")
             container = client.containers.get(str(str_array[1]))
             try:
                 container.remove()
                 response.message("The contaner has been removed permanently")
             except:
                 response.message("Please stop thee container before removing'")
         elif str_array[0] == "stop":
             # stop a container given ID or Name
             response.message("stopping...")
             container = client.containers.get(str(str_array[1]))
             try:
                 container.stop()
                 response.message("The container has been stopped!!")
             except:
                 response.message("The container has been sent to the brig")
         elif str_array[0] == "prune":
             # Does not work yet but should clear all stopped containers
             client.containers.prune()
             response.message("Destroyed all stopped containers")
         elif inbound_message == "docker help":
             response.message("To run a container: run (flags) (image); To rm a container: rm (container); To stop: stop (container); To list containers: ps (flags)")
         else:
             response.message("'tis be not a command. Walk th' plank")

    return Response(str(response), mimetype="application/xml"), 200


def parse_message(message):
    str_array = message.split(' ')
    if str_array[0] == "docker":
        del str_array[0]
    str_array[0] = str_array[0].lower()
    return str_array

def __help(message, response):
    stop_message = "To stop a container instance \n -> stop <container_name>:<version> or \n <container_id>:<version>"
    run_message = "To start a container instance \n -> run <image_name>:<version>. \n Default version 'latest'"
    del_message = "To remove a stopped container \n -> rm <container_name>:<version> or \n <container_id>:<version>"
    if message == 'run':
        response.message("***HELP PAGE***")
        response.message(run_message)
    elif message == 'stop':
        response.message("***HELP PAGE***")
        response.message(stop_message)
    elif message == 'rm':
        response.message("***HELP PAGE***")
        response.message(del_message)
    else:
       response.message("***INVALID REQUEST***")



if __name__ == '__main__':
    app.run(debug=True,host='127.0.0.1')
