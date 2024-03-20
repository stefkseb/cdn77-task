# CDN77 - task

According to the task, I created Ansible playbook that automatically sets up the whole infrastructure, installs and configures services and starts them. There is one playbook in the root directory `main.yml`, which is supposed to be run and multiple Ansible roles which are gradually launched. Each role will be described later. I tried to follow Ansible best practises, when it comes to the structure of the roles. Roles should be reusable and universal, so that I could easily use them in a different project. Configuration files are prepared using templates (jinja2 templating) and using ansible facts and magic variables, so that one template can be used in multiple instances of the same service. 

### Prerequisities

A machine with Debian 12, ideally 16 GB of RAM and ansible installed on it.

### How to run

Execute the following command on the machine in the directory with the task files

`ansible-playbook -i inventory.ini main.yml`

### Infrastructure

I decided to build the infrastructure using docker containers, because they can be spun up fast and easily recreated. Also running to many full VMs would be too much for my computer. Although it is not the traditional use of docker, as I did not use prebuilt containers from dockerhub so I could use Ansible to set up everything manually. Docker is supposed to be used that one container runs one service, which was not respected and I am aware of it.

## Ansible inventory
There is one simple `inventory.ini`, which groups containers according to the services that run on them. Variables for individual inventory groups are in the `group_vars` directory.

## Description of roles

### installDocker

On the host machine on which the main playbook is run this role installs docker and some other dependencies for it.

### createInfra

First a custom docker image is built. It is based on Debian 12. Python and ssh server are added to the image. It is called *generic_img* and it is used for all instances of containers set up later.

A custom docker network is created in IP range `192.168.0.0/24`. Then the containers for individual services are created.

SSH key `containers_key` is the same for every container. The public key is mounted into the container.

### installAndConfigurePrometheus

Prometheus and Alertmanager are installed. For their configuration I used templates. `prometheus-node-exporter` is installed in every contrainer and it collects basic metrics from them. 

I set up one rule checking load of the containers and in case of high load an alert is triggered. Alertmanager will send and email. (For testing purposes a public testing smtp server was used) Also alerting like sending a message to Slack, MS Teams or an SMS could be used, but again for simplicity email was chosen. 

In case configuration changes, handler is triggered to restart the services.

### installNginx

Installs two instances of `nginx` and `prometheus-nginx-exporters`

### configureNginxWebserver

This role removes default website, copies configuration file using templates. A webserver hosting local files is run on port 80 and stub_status module on port 8080.

### configureNginxRProxy

Reverse caching proxy is set up using as upstream the previously configured nginx instance. Pregenerated certificates are copied into the container. Ideally on an instance with a registered domain name an automatic request and installation of a certificate from a CA would be made. Also automatic checking of a validity of the certificate and auto renewal would be convinient. Proxy caches the data in /tmp. For client <> proxy a TLS connection is available on `https://<host_ip>`. For proxy <> upstream keepalive connections are used.

## installElastic

For the distributed system I chose to run Elasticsearch cluster, as I have come accross this technology in the past. There are total of 5 instances configured, all are master eligible and data nodes. Each instance also runs `prometheus-elasticsearch-exporter`.

For the cluster to be resilient to the outage of 2 instances, majority of nodes have to be present, so that the master can be voted. The number of replicas to the `my-index` is set to 2, therefore I have 3 copies of the data on different instances.

### installDaemon

The custom daemon is a script written in python running in the prometheus container. I used python as I have most expirience in it than in other languages. It fetches load of individual containers from prometheus using prometheus HTTP API and also statistics from the nginx proxy from the stub module with the reaponse headers. It creates a file  `/var/log/stats.json` in the prometheus container. It shall be human readable and well machine processable. JSON format, when it is not too complex and not too nested is well human readable, maybe other formats considered were yaml or even CSV. Example of the `stats.json`:

```
{
    "monitoring": {
        "192.168.0.2:9100": 0.68,
        "192.168.0.3:9100": 0.68,
        "192.168.0.4:9100": 0.74,
        "192.168.0.5:9100": 0.74,
        "192.168.0.6:9100": 0.68,
        "192.168.0.7:9100": 0.63,
        "192.168.0.8:9100": 0.74,
        "192.168.0.9:9100": 0.74
    },
    "nginx": {
        "response_headers": {
            "Server": "nginx/1.22.1",
            "Date": "Tue, 19 Mar 2024 14:55:12 GMT",
            "Content-Type": "text/plain",
            "Content-Length": "97",
            "Connection": "keep-alive"
        },
        "stats": {
            "connections": "2",
            "accepts": "7",
            "handled": "7",
            "requests": "9",
            "reading": "0",
            "writing": "1",
            "waiting": "1"
        }
    }
}
```
The script runs as a daemon and is managed by the daemontools. Once it is in place, `svscanboot` is started and automatically checks services in the `/etc/services` directory. It runs them and checks them. If they fail, it tries to start them again.
