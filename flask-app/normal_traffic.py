import requests
import random
import time


BASE_URL = "http://localhost:5000"


def request(method, endpoint, **kwargs):

    try:

        response = requests.request(
            method,
            BASE_URL + endpoint,
            timeout=3,
            **kwargs
        )

        print(
            f"{method:6} "
            f"{endpoint:35} "
            f"{response.status_code}",
            flush=True
        )

        return response

    except Exception as e:

        print(
            f"ERROR {method} {endpoint}: {e}",
            flush=True
        )

        return None


def normal_session():

    request("GET", "/health")

    time.sleep(
        random.uniform(0.001, 0.2)
    )

    request(
        "POST",
        "/api/login",
        json={
            "username": "alice",
            "password": "password"
        }
    )

    time.sleep(
        random.uniform(0.001, 0.2)
    )

    request(
        "GET",
        "/api/profile"
    )

    time.sleep(
        random.uniform(0.001, 0.2)
    )

    request(
        "GET",
        "/api/products"
    )

    time.sleep(
        random.uniform(0.001, 0.2)
    )

    if random.random() < 0.7:

        queries = [
            "laptop",
            "mouse",
            "keyboard",
            "monitor",
            "ssd",
            "usb"
        ]

        query = random.choice(queries)

        request(
            "GET",
            "/api/search",
            params={
                "q": query
            }
        )

        time.sleep(
            random.uniform(0.001, 0.2)
        )

    product_ids = random.sample(
        list(range(1, 9)),
        random.randint(1, 4)
    )

    for product_id in product_ids:

        request(
            "GET",
            f"/api/products/{product_id}"
        )

        time.sleep(
            random.uniform(0.001, 0.2)
        )

    request(
        "GET",
        "/api/cart"
    )

    time.sleep(
        random.uniform(0.001, 0.2)
    )


    if random.random() < 0.6:

        product_id = random.choice(
            [2, 3, 4, 5, 6, 7, 8]
        )

        quantity = random.randint(1, 2)

        request(
            "POST",
            "/api/cart/add",
            json={
                "product_id": product_id,
                "quantity": quantity
            }
        )

        time.sleep(
            random.uniform(0.001, 0.2)
        )

        request(
            "GET",
            "/api/cart"
        )

    time.sleep(
        random.uniform(0.001, 0.2)
    )

    request(
        "GET",
        "/api/orders"
    )

    time.sleep(
        random.uniform(0.001, 0.2)
    )

    # Sometimes open an existing order
    if random.random() < 0.6:

        order_id = random.choice(
            [1001, 1002]
        )

        request(
            "GET",
            f"/api/orders/{order_id}"
        )

    if random.random() < 0.3:

        request(
            "POST",
            "/api/orders",
            json={
                "items": [
                    {
                        "product_id": random.randint(1, 8),
                        "quantity": 1
                    }
                ]
            }
        )

    time.sleep(
        random.uniform(0.001, 0.2)
    )

    request(
        "POST",
        "/api/logout"
    )


def run_normal_traffic():

    print(
        "Starting continuous normal traffic generation...",
        flush=True
    )

    try:
        while True:

            normal_session()

    except KeyboardInterrupt:

        print(
            "\nStopping continuous normal traffic generation.",
            flush=True
        )


if __name__ == "__main__":
    run_normal_traffic()