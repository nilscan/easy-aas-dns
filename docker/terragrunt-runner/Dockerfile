FROM alpine:3

ARG ARCH=amd64
ARG TERRAGRUNT_VERSION=v0.48.1
ARG TFSWITCH_VERSION=latest
ARG TERRAFORM_ROOT_DIR=/terraform

# The terraform bin dir is not user overridable in current version of tfswitch
ENV PATH=$PATH:/home/tfuser/bin
# Base dir for the terraform root config
ENV TERRAFORM_ROOT_DIR=$TERRAFORM_ROOT_DIR
# Subdirectory under $TERRAFORM_ROOT_DIR for the terraform root config
ENV TERRAFORM_DIR=

RUN addgroup -S tfuser && adduser -S tfuser -G tfuser

# Install dependencies
RUN apk add --update --no-cache bash git openssh curl ca-certificates libc6-compat && update-ca-certificates

# Install terragrunt
RUN TERRAGRUNT_URL="https://github.com/gruntwork-io/terragrunt/releases/download/${TERRAGRUNT_VERSION}/terragrunt_linux_${ARCH}" \
    && wget -q "${TERRAGRUNT_URL}" -O /usr/local/bin/terragrunt \
    && chmod +x /usr/local/bin/terragrunt

# Install tfswitch
RUN curl -L --proto "=https" --tlsv1.2 https://raw.githubusercontent.com/warrensbox/terraform-switcher/release/install.sh | sh

ADD run.sh /app/run.sh
RUN chown 1001:1001 /app/run.sh && chmod +x /app/run.sh
RUN mkdir -p "${TERRAFORM_ROOT_DIR}" && chown tfuser:tfuser "${TERRAFORM_ROOT_DIR}"

USER tfuser
WORKDIR $TERRAFORM_ROOT_DIR

# Preinstall the latest terraform
RUN tfswitch --latest

ENTRYPOINT ["/app/run.sh"]
