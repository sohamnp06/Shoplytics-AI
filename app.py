from flask import Flask, request, render_template
from etl.transform import transform_single
from etl.validate import validate_data
from etl.load import load_data

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/submit", methods=["POST"])
def submit():

    try:
        data = request.form.to_dict()

        # -------------------------
        # TYPE CONVERSION
        # -------------------------
        float_fields = [
            "Age", "Unit_Price", "Quantity", "Discount_Amount",
            "Total_Amount", "Session_Duration_Minutes",
            "Pages_Viewed", "Delivery_Time_Days", "Customer_Rating"
        ]

        for field in float_fields:
            if field in data:
                if data[field] == "":
                    data[field] = 0
                else:
                    data[field] = float(data[field])

        # -------------------------
        # BOOLEAN FIX (CRITICAL)
        # -------------------------
        data["Is_Returning_Customer"] = True if data.get("Is_Returning_Customer") == "1" else False

        # -------------------------
        # ETL FLOW
        # -------------------------
        df = transform_single(data)
        validate_data(df)
        load_data(df, mode="append")

        return render_template("index.html", message="✅ Data inserted successfully!")

    except Exception as e:
        return render_template("index.html", message=f"❌ Error: {str(e)}")


if __name__ == "__main__":
    app.run(debug=True)