# Sensor Tracking System

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-username/sensor-tracking-system.git
   ```
2. Navigate to the project directory:
   ```
   cd sensor-tracking-system
   ```
3. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```
4. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Run the application:
   ```
   python app.py
   ```
6. Access the application in your web browser at `http://localhost:5000`.

## Usage

The Sensor Tracking System provides a web-based interface to monitor and manage sensor data. The main features include:

- Live data monitoring for multiple sensors
- Historical data visualization and analysis
- Sensor calibration management
- Data export to CSV and Excel formats

## API

The application exposes the following API endpoints:

- `/api/sensors`: Retrieve a list of all registered sensors
- `/api/sensor/<sensor_id>/data`: Retrieve sensor data for a specific sensor
- `/api/calibration/<sensor_id>`: Retrieve calibration data for a specific sensor
- `/api/calibration/<sensor_id>`: Update calibration parameters for a specific sensor

## Contributing

Contributions to the Sensor Tracking System are welcome. To contribute, please follow these steps:

1. Fork the repository
2. Create a new branch for your feature or bug fix
3. Make your changes and commit them
4. Push your changes to your forked repository
5. Submit a pull request to the main repository

## License

This project is licensed under the [MIT License](LICENSE).

## Testing

To run the tests for the Sensor Tracking System, use the following command:

```
python -m unittest discover tests/
```

This will run all the test cases located in the `tests/` directory.