from safely_report import app


@app.route("/")
def index():
    return "Welcome!"


if __name__ == "__main__":
    app.run(debug=True)
