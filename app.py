from flask import Flask, jsonify, request
from flask_mysqldb import MySQL
from flask_cors import CORS
import random

app = Flask(__name__)
CORS(app)

# -----------------------------
# MYSQL CONFIG
# -----------------------------
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'adityacr769'
app.config['MYSQL_DB'] = 'drone_system'

mysql = MySQL(app)

# -----------------------------
# DASHBOARD
# -----------------------------
@app.route("/dashboard")
def dashboard():
    cur = mysql.connection.cursor()

    cur.execute("SELECT COUNT(*) FROM operator")
    operators = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM drone")
    drones = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM violation")
    violations = cur.fetchone()[0]

    return jsonify({
        "operators": operators,
        "drones": drones,
        "violations": violations
    })

# -----------------------------
# OPERATORS
# -----------------------------
@app.route("/operators")
def get_operators():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM operator")
    data = cur.fetchall()

    result = []
    for row in data:
        result.append({
            "OperatorID": row[0],
            "Name": row[1],
            "ExperienceYears": row[2]
        })

    return jsonify(result)
# -----------------------------
# OPERATORS
# -----------------------------
@app.route("/risk/<operator_id>")
def risk(operator_id):
    try:
        cur = mysql.connection.cursor()

        # get operator experience
        cur.execute("SELECT ExperienceYears FROM operator WHERE OperatorID=%s", (operator_id,))
        exp = cur.fetchone()

        if not exp:
            return jsonify({"error": "Operator not found"}), 404

        # count violations
        cur.execute("""
            SELECT COUNT(*) 
            FROM violation v
            JOIN flight f ON v.FlightID = f.FlightID
            JOIN drone d ON f.DroneID = d.DroneID
            WHERE d.OperatorID=%s
        """, (operator_id,))

        violations = cur.fetchone()[0]

        # risk logic
        if violations > 2:
            risk_level = "HIGH"
        elif violations > 0:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return jsonify({
            "OperatorID": operator_id,
            "Violations": violations,
            "RiskLevel": risk_level
        })

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": str(e)}), 500

# -----------------------------
# DRONES
# -----------------------------
@app.route("/drones")
def get_drones():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM drone")
    data = cur.fetchall()

    result = []
    for row in data:
        result.append({
            "DroneID": row[0],
            "Model": row[1],
            "Type": row[2],
            "Status": row[3],
            "OperatorID": row[4]
        })

    return jsonify(result)

# -----------------------------
# FLIGHTS
# -----------------------------
@app.route("/flights")
def get_flights():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM flight")
    data = cur.fetchall()

    result = []
    for row in data:
        result.append({
            "FlightID": row[0],
            "DroneID": row[1],
            "Altitude": row[2],
            "ZoneID": row[3],
            "ControllerID": row[4],
            "Status": row[5]
        })

    return jsonify(result)

# -----------------------------
# VIOLATIONS
# -----------------------------
@app.route("/violations")
def get_violations():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM violation")
    data = cur.fetchall()

    result = []
    for row in data:
        result.append({
            "ViolationID": row[0],
            "FlightID": row[1],
            "Severity": row[2],
            "Penalty": row[3],
            "Reason": row[4]   # ✅ added
        })

    return jsonify(result)

# -----------------------------
# ADD OPERATOR
# -----------------------------
@app.route("/add_operator", methods=["POST"])
def add_operator():
    try:
        data = request.get_json()

        operator_id = data.get("OperatorID")
        name = data.get("Name")
        experience = data.get("ExperienceYears")

        # ✅ VALIDATION
        if not operator_id or not name or not experience:
            return jsonify({"error": "Missing fields"}), 400

        cur = mysql.connection.cursor()

        cur.execute(
            """
            INSERT INTO operator 
            (OperatorID, Name, ExperienceYears)
            VALUES (%s, %s, %s)
            """,
            (operator_id, name, experience)
        )

        mysql.connection.commit()

        return jsonify({"message": "Operator added"})

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": str(e)}), 500
# -----------------------------
# ADD FLIGHT (FINAL FIXED)
# -----------------------------
@app.route("/add_flight", methods=["POST"])
def add_flight():
    try:
        data = request.get_json()

        drone_id = data.get("DroneID")
        altitude = int(data.get("Altitude"))
        zone_id = data.get("ZoneID")
        status = data.get("Status")
        controller_id = data.get("ControllerID")

        cur = mysql.connection.cursor()

        # ✅ DEFINE VARIABLES (fix error)
        violation = False
        reason = ""

        # ✅ LOGIC
        if zone_id == "ZN03":
            violation = True
            reason = "No Fly Zone"
        elif altitude > 120:
            violation = True
            reason = "High Altitude"

        # ✅ UNIQUE FLIGHT ID
        flight_id = "FL" + str(random.randint(1000, 9999))

        # ✅ INSERT FLIGHT
        cur.execute(
            """
            INSERT INTO flight 
            (FlightID, DroneID, Altitude, ZoneID, ControllerID, Status)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (flight_id, drone_id, altitude, zone_id, controller_id, status)
        )

        # ✅ INSERT VIOLATION (FIXED WITH REASON)
        if violation:
            cur.execute(
                """
                INSERT INTO violation 
                (ViolationID, FlightID, Severity, Penalty, Reason)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    "V" + str(random.randint(10000, 99999)),
                    flight_id,
                    "High",
                    50000,
                    reason
                )
            )

        mysql.connection.commit()

        return jsonify({
            "message": "Flight added",
            "violation": violation,
            "reason": reason
        })

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": str(e)}), 500
# -----------------------------
# ADD FLIGHT (FINAL FIXED)
# -----------------------------
@app.route("/add_drone", methods=["POST"])
def add_drone():
    try:
        data = request.get_json()

        drone_id = data.get("DroneID")
        model = data.get("Model")
        drone_type = data.get("Type")
        status = data.get("Status")
        operator_id = data.get("OperatorID")

        cur = mysql.connection.cursor()

        cur.execute(
            """
            INSERT INTO drone 
            (DroneID, Model, Type, Status, OperatorID)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (drone_id, model, drone_type, status, operator_id)
        )

        mysql.connection.commit()

        return jsonify({"message": "Drone added"})

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": str(e)}), 500


# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5001)