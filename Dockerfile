FROM python:3.11-slim        # pake Python 3.11
WORKDIR /app                 # masuk ke folder /app di container
COPY requirements.txt .      # salin requirements.txt ke /app
RUN pip install -r requirements.txt  # install library di /app
COPY . .                     # salin semua file project kamu ke /app
CMD ["python", "main.py"]    # jalankan main.py dari /app
