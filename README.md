# The test-auth

## Table of Contents
**[Installation](#installation)**

**[Run Elasticsearch](#run-elasticsearch)**

**[Run API](#run-api)**

**[API Docs](#api-docs)**

**[Examples](#examples)**

## Installation
```
$ git clone https://github.com/korniichuk/test-auth.git
$ cd test-auth/
$ python3 -m venv venv
$ source venv/bin/activate
(venv) $ pip3 install -r requirements.txt
```

## Run Elasticsearch
```
$ docker pull docker.elastic.co/elasticsearch/elasticsearch:6.1.2
$ docker run -d -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" \
        docker.elastic.co/elasticsearch/elasticsearch:6.1.2
```

## Run API
Please, check one more time that Elasticsearch was ran successfully on http://localhost:9200/. Example output:
```
{
  "name" : "uEoEr2L",
  "cluster_name" : "docker-cluster",
  "cluster_uuid" : "HDd7eS2KSJaDgss13oBJ8Q",
  "version" : {
    "number" : "6.1.2",
    "build_hash" : "5b1fea5",
    "build_date" : "2018-01-10T02:35:59.208Z",
    "build_snapshot" : false,
    "lucene_version" : "7.1.0",
    "minimum_wire_compatibility_version" : "5.6.0",
    "minimum_index_compatibility_version" : "5.0.0"
  },
  "tagline" : "You Know, for Search"
}
```
```
(venv) $ python3 api.py
```

## API Docs
- POST **/api/auth/accounts**

    Sing Up. Register a new user.<br>
    The body must contain a JSON object that defines `company_name`, `contact_person`, `business_email`, `contact_phone_number`, and `password` fields.<br>
    On success a status code 201 is returned. The body of the response contains a JSON object with the newly added user.<br>
    On failure status code 400 (bad request) is returned.<br>
    Notes:
    - The password is hashed by scrypt KDF before it is stored in Elasticsearch. Once hashed, the original password is discarded.
    - In a production deployment secure HTTP must be used to protect the password in transit.
    - In a production deployment `md5` field based on secret key and `timestamp` field must be used. Example: [goo.gl/395zAB](https://goo.gl/395zAB).

- GET **/api/auth/token**

    Return an authentication token.<br>
    This request must be authenticated using a HTTP Basic Authentication header.<br>
    On success a JSON object is returned with a field `token` set to the authentication token for the user and a field `duration` set to the (approximate) number of seconds the token is valid.<br>
    On failure status code 401 (unauthorized) is returned.

- GET **/api/auth/protected**

    Return a protected resource.<br>
    This request must be authenticated using a HTTP Basic Authentication header. Instead of username and password, the client can provide a valid authentication token in the username field. If using an authentication token the password field is not used and can be set to any value.<br>
    On success a JSON object with data for the authenticated user is returned.<br>
    On failure status code 401 (unauthorized) is returned.

## Examples
Please import [test-auth.postman_collection.json](test-auth.postman_collection.json) file to [Postman](https://www.getpostman.com/).
