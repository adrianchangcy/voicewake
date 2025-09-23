FROM mcr.microsoft.com/devcontainers/base:ubuntu

ARG node_version=v24.7.0
ARG python_version=3.13.7

#host machine file paths are based on project root, defined at docker-compose.yaml build context

#bind mount not available here, so COPY first
#copy entire project root into /workspace
COPY . /workspace
WORKDIR /workspace

#node

#install curl, download prebuilt Node.js binary archive file
#extract files, symlink so node/npm/npx are accessible globally
RUN apt-get update -y && apt-get install curl -y \
&& curl -fsSL https://nodejs.org/dist/$node_version/node-$node_version-linux-x64.tar.gz -o node.tar.gz \
&& tar -xzvf node.tar.gz && rm node.tar.gz \
&& mv node-$node_version-linux-x64 /usr/local/node \
&& ln -s /usr/local/node/bin/node /usr/local/bin/node \
&& ln -s /usr/local/node/bin/npm /usr/local/bin/npm \
&& ln -s /usr/local/node/bin/npx /usr/local/bin/npx

#attempt #1 to fix "ERR_SSL_CIPHER_OPERATION_FAILED", not reliable, only worked once
#try next: https://stackoverflow.com/questions/79492995/npm-error-code-err-ssl-cipher-operation-failed-after-windows-11-update
RUN npm cache clear --force
RUN npm cache verify

WORKDIR /workspace/frontend
RUN npm install --verbose

#python

WORKDIR /workspace

#base images have issues with you directly installing python packages, due to possible conflict with pre-installed ones (if any)
RUN apt-get install python3 -y
RUN apt-get install python3-pip -y
RUN apt-get install virtualenv -y
#set up /workspace/.venv folder
RUN virtualenv .venv
#tell pip which .venv to use, which in this case is the one in project root
ENV VIRTUAL_ENV=/workspace/.venv
ENV PATH="/workspace/.venv/bin:$PATH"
RUN pip install -r requirements.txt --no-cache-dir --verbose --default-timeout=100

ENTRYPOINT sleep infinity