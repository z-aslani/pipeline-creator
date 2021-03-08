FROM reg.pegah.tech/common/maven:
LABEL MAINTAINER="PegahTech Co."

ADD target/JAR_FILE_NAME.jar /data/JAR_FILE_NAME.jar
WORKDIR /data

RUN mkdir /tz && mv /etc/timezone /tz/ && mv /etc/localtime /tz/ && ln -s /tz/timezone /etc/ && ln -s /tz/localtime /etc/
RUN echo "Asia/Tehran" > /etc/timezone && dpkg-reconfigure -f noninteractive tzdata && cp /etc/localtime /tz/
VOLUME /tz
ENV CONFIG_MODE production

CMD exec java -Djava.util.concurrent.ForkJoinPool.common.parallelism=50 ${JAVA_OPTS} -jar JAR_FILE_NAME.jar --spring.config.name=${CONFIG_MODE} # and some args here
