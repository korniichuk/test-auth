#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from elasticsearch import Elasticsearch
from flask import abort, Flask, g, jsonify, request
from flask_httpauth import HTTPBasicAuth
from itsdangerous import (TimedJSONWebSignatureSerializer as
        Serializer, BadSignature, SignatureExpired)
from pylibscrypt import scrypt_mcf, scrypt_mcf_check

app = Flask(__name__)
app.config["SECRET_KEY"] = "Enter your secret key here..."
auth = HTTPBasicAuth()
es = Elasticsearch()
mapping = {"mappings": {"company": {"properties": {"company_name": {"type":
        "keyword", "index": True}, "business_email": {"type": "keyword",
        "index": True}}}}}
es.indices.create(index="accounts", ignore=400, body=mapping)

@auth.verify_password
def verify_password(company_name_or_token, password):
    """Verify password of account"""

    def check_password(hash, password):
        hash_bytes = hash.encode("utf-8", "ignore")
        password_bytes = password.encode("utf-8", "ignore")
        return scrypt_mcf_check(hash_bytes, password_bytes)

    def check_auth_token(token):
        s = Serializer(app.config["SECRET_KEY"])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None # valid expired token
        except BadSignature:
            return None # invalid token
        company_name = data["company_name"]
        return company_name

    # Try to authenticate by auth token
    company_name = check_auth_token(company_name_or_token)
    if not company_name:
        # Try to authenticate with company_name and password
        company_name = company_name_or_token
        try:
            body = {"query": {"constant_score": {"filter": {"term": {
                    "company_name": company_name}}}}}
            res = es.search(index="accounts", doc_type="company", body=body)
        except Exception as e:
            app.logger.error("MatchCompanyNameError")
            abort(400)
        else:
            exists = res["hits"]["total"]
            if not exists:
                return False # not existing company
            else:
                hash = res["hits"]["hits"][0]["_source"]["password"]
                if not check_password(hash, password):
                    return False # wrong password
    g.company_name = company_name
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
    hash = scrypt_mcf(password_bytes).decode("utf-8", "ignore")
    # Check requered fields
    if ((company_name is None) or (contact_person is None) or
            (business_email is None) or (contact_phone_number is None) or
            (password is None)):
        abort(400) # missing arguments
    # Check company_name in Elasticsearch
    try:
        body = {"query": {"constant_score": {"filter": {"term": {
                "company_name": company_name}}}}}
        res = es.search(index="accounts", doc_type="company", body=body)
    except Exception as e:
        app.logger.error("MatchCompanyNameError")
        abort(400)
    else:
        exists = res["hits"]["total"]
        if exists:
            abort(400) # existing company
    # Check business_email in Elasticsearch
    try:
        body = {"query": {"constant_score": {"filter": {"term": {
                "business_email": business_email}}}}};
        res = es.search(index="accounts", doc_type="company", body=body)
    except Exception as e:
        app.logger.error("MatchBusinessEmailError")
        abort(400)
    else:
        exists = res["hits"]["total"]
        if exists:
            abort(400) # existing business_email
    # Add company to elasticsearch
    try:
        body={"company_name": company_name, "contact_person": contact_person,
              "business_email": business_email,
              "contact_phone_number" : contact_phone_number, "password": hash}
        res = es.create(index="accounts", doc_type="company", id=company_name,
                        body=body)
    except Exception as e:
        app.logger.error("CreatCompanyError")
        abort(400)
    return (jsonify({"company_name": company_name})), 201

@app.route("/api/auth/token")
@auth.login_required
def get_auth_token():
    """Get auth token"""

    def generate_auth_token(company_name, expiration=600):
        s = Serializer(app.config["SECRET_KEY"], expires_in=expiration)
        return s.dumps({"company_name": company_name})

    token = generate_auth_token(g.company_name)
    return jsonify({"token": token.decode("ascii"), "duration": 600})

@app.route("/api/auth/protected")
@auth.login_required
def get_protected_resource():
    """Get protected resource"""

    return jsonify({"company_name": g.company_name})

if __name__ == "__main__":
    app.run(debug=True)
