from flask import Flask, render_template, url_for, request, jsonify

app = Flask(__name__)

@app.route("/")
def main_page():
    print("Page is working")
    return render_template("index.html")

@app.route('/process', methods=["GET", "POST"])
def background_process_test():
    if request.method == "POST":
        data = request.get_json()
        print (type(data))
        if data == "F" : 
            print("the machine moves forward")
    return ("nothing")

if __name__ == "__main__":
    app.run(debug=True)