# 1. Gunakan Python versi ringan (Slim)
FROM python:3.10-slim

# 2. Set variabel environment agar Python tidak membuat file cache (.pyc)
#    dan output log langsung muncul (unbuffered)
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Set folder kerja di dalam container
WORKDIR /code

# 4. Install dependencies sistem yang dibutuhkan untuk Postgres & build tools
RUN apt-get update \
    && apt-get install -y postgresql-client libpq-dev gcc \
    && apt-get clean

# 5. Copy file requirements dulu (biar caching Docker optimal)
COPY requirements.txt /code/

# 6. Install library Python
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 7. Copy seluruh sisa kodingan project
COPY . /code/

# 8. Command untuk menjalankan aplikasi saat container start
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]