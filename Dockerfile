FROM python:3.11-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8080
WORKDIR /app
COPY requirements-linux.lock ./
RUN pip install --no-cache-dir -r requirements-linux.lock && useradd --create-home appuser
COPY --chown=appuser:appuser app.py ./
COPY --chown=appuser:appuser src ./src
COPY --chown=appuser:appuser views ./views
COPY --chown=appuser:appuser cloud ./cloud
COPY --chown=appuser:appuser scripts/start_app.py ./scripts/start_app.py
COPY --chown=appuser:appuser .streamlit/config.toml ./.streamlit/config.toml
COPY --chown=appuser:appuser models ./models
COPY --chown=appuser:appuser artifacts/*.json artifacts/historical_predictions.csv artifacts/historical_probabilities.csv ./artifacts/
USER appuser
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.getenv('PORT','8080')+'/_stcore/health',timeout=3)"
CMD ["python", "scripts/start_app.py"]
