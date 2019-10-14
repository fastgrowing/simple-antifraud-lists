FROM python:3.7.1-alpine3.8

RUN mkdir -p /opt/antifraud && \
    addgroup antifraud && \
    adduser -D -S -G antifraud antifraud -h /opt/antifraud && \
    apk add --no-cache gcc musl-dev make && \
    chown -R antifraud:antifraud /opt/antifraud

USER antifraud

WORKDIR /opt/antifraud

COPY --chown=antifraud:antifraud requirements.txt /opt/antifraud/

RUN pip install --user -r requirements.txt

COPY --chown=antifraud:antifraud . /opt/antifraud/

EXPOSE 80

CMD ["python3", "app.py"]
