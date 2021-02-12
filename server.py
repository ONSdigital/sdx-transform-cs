from transform import app

if __name__ == '__main__':
    port = 5000
    app.run(debug=True, host='0.0.0.0', port=port)
