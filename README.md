# CDN77 - task

According to the task, I created Ansible playbook that automatically sets up the whole infrastructure, installs and configures services and starts them. There is one playbook in the root directory `main.yml`, which is supposed to be run and multiple Ansible roles which are gradually launched. Each role will be described later. I tried to follow Ansible best practises, when it comes to the structure of the roles.

### Prerequisities

A machine with Debian 12, ideally 16 GB of RAM and ansible installed on it.

### How to run

Execute the following command on the machine in the directory with the task files

`ansible-playbook -i inventory.ini main.yml`

### Infrastructure

I decided to build the infrastructure using docker containers. However it is not the traditional use of docker, as I did not use prebuilt containers from dockerhub so I could use Ansible to set up everything manually.

## Ansible inventory
There is one simple `inventory.ini`, which groups containers according to the services that run on them. Variables for individual inventory groups are in the `group_vars` directory.

## Description of roles

### installDocker

On the host machine on which the main playbook is run this role installs docker and some other dependencies for it.

### createInfra

First a custom docker image is built. It is based on the Debian 12. Python and ssh server are added to the image. It is called *generic_img* and it is used for all instances of services set up later.

A custom docker network is created in IP range `192.168.0.0/24`. Then the containers for individual services are created.

SSH key `containers_key` is the same for every container. The public key is mounted into the container.

### installAndConfigurePrometheus

Prometheus and Alertmanager are installed. For their configuration I used templates. `prometheus-node-exporter` is installed in every contrainer and it collects basic metrics from them. 

I set up one rule checking load of the containers and in case of high load an alert is triggered. Alertmanager will send and email. (For testing purposes some testing smtp server was used)

In case configuration changes, handler is triggered to restart the services.

### installNginx

Installs two instances of `nginx` and `prometheus-nginx-exporters`

### configureNginxWebserver

This role removes default website, copies configuration file using templates. A webserver hosting local files is run on port 80 and stub_status module on port 8080.

### configureNginxRProxy

Reverse caching proxy is set up using as upstream the previously configured nginx instance. Pregenerated certificates are copied into the container. Proxy caches the data in /tmp. For client <> proxy a TLS connection is available on `https://<host_ip>`. For proxy <> upstream keepalive connections are used.

## installElastic

For the distributed system I chose to run Elasticsearch cluster. There are total of 5 instances configured. Each instance also runs `prometheus-elasticsearch-exporter`.

For the cluster to be resilient to the outage of 2 instances, majority of nodes have to be present, so that the master can be voted. The number of replicas to the `my-index` is set to 2.

### installDaemon

The custom daemon is a script written in python running in the prometheus container. It fetches load of individual containers from prometheus and also statistics from the nginx proxy from the stub module with the reaponse headers. It creates a file  `/var/log/stats.json` in the prometheus container. It shall be human readable and well machine processable. Example of the `stats.json`:

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
The script runs as a daemon and is managed by the daemontools. Once it is in place `svscanboot` is started and automatically checks services in the `/etc/services` directory.