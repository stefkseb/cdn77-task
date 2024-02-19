FROM debian:bookworm

# Install openssh server
RUN     apt -y update && \
        apt -y install openssh-server python3

RUN     mkdir /var/run/sshd

RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

CMD [ "/usr/sbin/sshd", "-D" ]