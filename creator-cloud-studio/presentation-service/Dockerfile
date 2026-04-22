FROM public.ecr.aws/docker/library/python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
COPY templates/ templates/
EXPOSE 5000
CMD ["python", "app.py"]