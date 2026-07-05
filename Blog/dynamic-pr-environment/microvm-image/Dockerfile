FROM public.ecr.aws/lambda/microvms:al2023-minimal

# System deps
RUN microdnf install -y python3 python3-pip && microdnf clean all

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
WORKDIR /app
COPY app.py .

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--timeout", "120", "app:app"]
