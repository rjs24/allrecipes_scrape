FROM python:3

WORKDIR /sur/src/app
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python3", "./allrecipes/spider_starter.py"]