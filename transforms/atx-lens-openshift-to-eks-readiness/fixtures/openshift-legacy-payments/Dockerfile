# syntax=docker/dockerfile:1
FROM registry.access.redhat.com/ubi9/openjdk-21:1.20

USER root
RUN mkdir -p /var/lib/payments/spool \
    && chown -R 1001:0 /var/lib/payments \
    && chmod -R 0750 /var/lib/payments

COPY target/payments-*.jar /deployments/payments.jar

USER 1001
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/deployments/payments.jar"]
