from flask import Flask, request, jsonify
import math
import time
from prometheus_client import Counter, Histogram, make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware
import prometheus_client

# Initialize Flask app
app = Flask(__name__)

# Define Prometheus metrics
REQUESTS = Counter(
    'factorial_requests_total',
    'Total number of factorial requests',
    ['endpoint', 'http_status']
)

EXCEPTIONS = Counter(
    'factorial_exceptions_total',
    'Total number of exceptions during factorial computation',
    ['exception_type']
)

LATENCY = Histogram(
    'factorial_request_latency_seconds',
    'Time spent processing factorial request',
    ['endpoint'],
    buckets=(0.1, 0.5, 1.0, 2.0, 3.0, 4.0, 5.0, float('inf'))
)

def compute_factorial(n):
    """Compute the factorial of n with a simulated delay."""
    time.sleep(2)  # Delay for 2 seconds
    return math.factorial(n)

@app.route('/factorial', methods=['GET'])
def factorial():
    start_time = time.time()
    try:
        number = int(request.args.get('number', ''))
        if number < 0:
            REQUESTS.labels(endpoint='/factorial', http_status=400).inc()
            return jsonify({"error": "Please provide a non-negative integer."}), 400

        result = compute_factorial(number)
        REQUESTS.labels(endpoint='/factorial', http_status=200).inc()
        response = jsonify({"number": number, "factorial": result})

    except ValueError as e:
        EXCEPTIONS.labels(exception_type='ValueError').inc()
        REQUESTS.labels(endpoint='/factorial', http_status=400).inc()
        response = jsonify({"error": "Invalid input. Please provide an integer."}), 400

    except Exception as e:
        EXCEPTIONS.labels(exception_type='UnexpectedError').inc()
        REQUESTS.labels(endpoint='/factorial', http_status=500).inc()
        response = jsonify({"error": "Internal server error"}), 500

    finally:
        LATENCY.labels(endpoint='/factorial').observe(time.time() - start_time)

    return response

# Add prometheus wsgi middleware to expose metrics
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': make_wsgi_app()
})

if __name__ == '__main__':
    # Start up the server to expose metrics.
    app.run(host='0.0.0.0', port=5000)  
