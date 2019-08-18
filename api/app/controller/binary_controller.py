"""
isadetect - "ML-based ISA detection (architecture and endianness of binary code/sequences)"

Copyright (C) Sami Kairajarvi <sami.kairajarvi@gmail.com>, 2019

See COPYRIGHT, AUTHORS, LICENSE for more details.
"""

from flask_restplus import Resource
from app.model.binary import BinaryDTO
import http
import pandas as pd
import numpy
from flask import request
from flask_restplus import Resource
from app.helpers.calculate_features import UNKNOWN_ARCHITECTURE, get_architecture, calculate_features
from sklearn.externals import joblib
import os
import sys

api = BinaryDTO.api
parser = BinaryDTO.parser
binary_output = BinaryDTO.binary_output

if "ISADETECT_MODEL_FILE" not in os.environ:
    sys.exit("Missing environment value ISADETECT_MODEL_FILE")
else:
    try:
        model = joblib.load(os.environ["ISADETECT_MODEL_FILE"])
    except:
        sys.exit("Failed to load model: " + os.environ["ISADETECT_MODEL_FILE"])


@api.route('/')
class BinaryUpload(Resource):
    @api.expect(parser)
    @api.response(http.HTTPStatus.OK, 'Success', binary_output)
    def post(self):
        # Read uploaded file into memory
        binary = request.files["binary"].read()
        form = request.form
        print("API key is", form["api_key"])

        # Calculate features out of the binary
        features = calculate_features(binary)

        # Transform features into pandas dataframe
        query_df = pd.DataFrame([features])
        query = pd.get_dummies(query_df)

        # Use trained model to predict the architecture
        prediction = model.predict(query).astype(numpy.int64)
        prediction_int = prediction[0].item()

        # If the architecture is unknown, return it
        if prediction_int == UNKNOWN_ARCHITECTURE:
            return {"prediction": "unknown", "prediction_probability": 1}

        # Calculate prediction probability
        prediction_proba = model.predict_proba(query)
        probability = prediction_proba[0][prediction_int - 1]

        # Fetch the string representation of the architecture
        return {"prediction": get_architecture(prediction_int), "prediction_probability": probability}