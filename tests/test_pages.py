# import pytest
# from requests import HTTPError
#
# from tests.conftest import customer_data
#
#
# def test_customer_signup(client):
#     customer_d = customer_data()
#     response = client.post("/customers/", json=customer_d.dict())
#     customer = response.json()
#     assert customer["id"]
#
#
# def test_customer_signup_with_repeated_email(client):
#     customer_1 = customer_data().dict()
#     customer_2 = customer_data().dict()
#     customer_2["email"] = customer_1["email"]
#
#     _ = client.post("/customers/", json=customer_1)
#     response = client.post("/customers/", json=customer_2)
#
#     with pytest.raises(HTTPError):
#         response.raise_for_status()
#
#     assert response.status_code == 409
#
#
# def test_customer_signup_without_name(client):
#     customer_1 = customer_data().dict()
#     del customer_1["name"]
#
#     response = client.post("/customers/", json=customer_1)
#
#     with pytest.raises(HTTPError):
#         response.raise_for_status()
#
#     assert response.status_code == 400
