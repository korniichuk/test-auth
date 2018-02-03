#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from elasticsearch import Elasticsearch
from flask import abort, Flask, g, jsonify, request
from flask_httpauth import HTTPBasicAuth
from pylibscrypt import scrypt_mcf, scrypt_mcf_check

app = Flask(__name__)
auth = HTTPBasicAuth()
es = Elasticsearch()
mapping = {"mappings": {"company": {"properties": {"company_name": {"type":
        "keyword", "index": True}, "business_email": {"type": "keyword",
        "index": True}}}}}
es.indices.create(index="accounts", ignore=400, body=mapping)

@auth.verify_password
def verify_password(company_name, password):
    """Verify password of account"""

    def check_password(password):
        hash_str = res["hits"]["hits"][0]["_source"]["password"]
        hash_bytes = hash_str.encode("utf-8", "ignore")
        password_bytes = password.encode("utf-8", "ignore")
        return scrypt_mcf_check(hash_bytes, password_bytes)

    try:
        body = {"query": {"constant_score": {"filter": {"term": {
                "company_name": company_name}}}}}
        res = es.search(index="accounts", doc_type="company", body=body)
    except Exception as e:
        app.logger.error("MatchCompanyNameError")
        abort(400)
    else:
        if (res["hits"]["total"] == 0) or not check_password(password):
            return False # not existing company or wrong password
    g.user = company_name
    return True

@app.route("/api/auth/accounts", methods=["POST"])
def new_account():
    """Sing Up"""

    company_name = request.json.get("company_name")
    contact_person = request.json.get("contact_person")
    business_email = request.json.get("business_email")
    contact_phone_number = request.json.get("contact_phone_number")
    password = request.json.get("password")
    # Password hash by scrypt function
    password_bytes = password.encode("utf-8", "ignore")
    hash_str = scrypt_mcf(password_bytes).decode("utf-8", "ignore")
    # Check requered fields
    if ((company_name is None) or (contact_person is None) or
            (business_email is None) or (contact_phone_number is None) or
            (password is None)):
        abort(400) # missing arguments
    # Check company_name in elasticsearch
    try:
        body = {"query": {"constant_score": {"filter": {"term": {
                "company_name": company_name}}}}}
        res = es.search(index="accounts", doc_type="company", body=body)
    except Exception as e:
        app.logger.error("MatchCompanyNameError")
        abort(400)
    else:
        if res["hits"]["total"] > 0:
            abort(400) # existing company
    # Check business_email in elasticsearch
    try:
        body = {"query": {"constant_score": {"filter": {"term": {
                "business_email": business_email}}}}};
        res = es.search(index="accounts", doc_type="company", body=body)
    except Exception as e:
        app.logger.error("MatchBusinessEmailError")
        abort(400)
    else:
        if res["hits"]["total"] > 0:
            abort(400) # existing business_email
    # Add company to elasticsearch
    try:
        body={"company_name": company_name, "contact_person": contact_person,
              "business_email": business_email,
              "contact_phone_number" : contact_phone_number,
              "password": hash_str}
        res = es.create(index="accounts", doc_type="company", id=company_name,
                        body=body)
    except Exception as e:
        app.logger.error("CreatCompanyError")
        abort(400)

    return (jsonify({"company_name": company_name}))

@app.route("/api/auth/protected")
@auth.login_required
def get_resource():
    return "Hello, World"

if __name__ == "__main__":
    app.run(debug=True)
