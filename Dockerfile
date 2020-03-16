FROM python:3.8.2-buster

COPY requirements.txt /var/requirements.txt
RUN python3.8 -m pip install --requirement /var/requirements.txt

COPY src/ /var/code/
CMD ["python3.8", "/var/code/app.py"]
