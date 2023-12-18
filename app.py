from safely_report import create_app

app = create_app()


@app.route("/")
def index():
    return "Welcome!"


if __name__ == "__main__":
    app.run(debug=True)
