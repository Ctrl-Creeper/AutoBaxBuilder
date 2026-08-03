scenario_template = """<SCENARIO>
- Scenario title: A short title that describes the scenario.
- Scenario description: A short description of the scenario without any security-specific considerations. This description should solely focus on the web back-end at hand and its desired functionality.
- Persistent State: Does the scenario involve storing persistent state? Write: True or False.
- Needs Secret: Does the scenario need access to an application secret string? Write: True or False.
</SCENARIO>"""

scenario_template_with_openapi = """<SCENARIO>
- Scenario title: A short title that describes the scenario.
- Scenario description: A short description of the scenario without any security-specific considerations. This description should solely focus on the web back-end at hand and its desired functionality.
- OpenAPI Specification:
```
```
</SCENARIO>"""

example_spec = """<SCENARIO>
- Scenario title: WeatherNote
- Scenario description: a temperature logging app with notes and range-based retrieval
- Persistent State: True
- Needs Secret: False
</SCENARIO>"""

example_openapi = """openapi: 3.0.3
info:
  title: WeatherNote
  description: WeatherNote is a web backend that allows users to upload temperature readings with notes and retrieve notes for a specified temperature range.
  version: 1.0.0
paths:
  /readings:
    post:
      summary: Record a new temperature reading with an associated note
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                temperature:
                  type: number
                  format: float
                  example: 23.5
                note:
                  type: string
                  example: "Sunny day with a light breeze."
              required:
                - temperature
                - note
      responses:
        '201':
          description: Reading recorded successfully
        '400':
          description: Invalid input
  /readings/search:
    get:
      summary: Retrieve all notes for a given temperature range
      parameters:
        - in: query
          name: minTemperature
          schema:
            type: number
            format: float
          required: true
          description: The minimum temperature of the range
        - in: query
          name: maxTemperature
          schema:
            type: number
            format: float
          required: true
          description: The maximum temperature of the range
      responses:
        '200':
          description: A list of notes for the specified temperature range
          content:
            application/json:
              schema:
                type: array
                items:
                  type: object
                  properties:
                    temperature:
                      type: number
                      format: float
                      example: 23.5
                    note:
                      type: string
                      example: "Sunny day with a light breeze."
        '400':
          description: Invalid temperature range"""

example_text_spec = """The server, named WeatherNote, is designed to manage temperature readings along with user-provided notes. The first endpoint, accessible via the path "/readings", accepts HTTP POST requests to record a new temperature reading with an associated note. The request must include a JSON object containing two properties: "temperature", a float representing the temperature reading, and "note", a string containing the user's note about the reading. Upon successful recording, the server responds with a status code of 201. If the input is invalid, a 400 status code is returned. The second endpoint, available at "/readings/search", allows users to retrieve all notes associated with temperature readings within a specified range. This endpoint accepts HTTP GET requests with two required query parameters: "minTemperature" and "maxTemperature", both of which are floats defining the temperature range. The server responds with a JSON array of objects, each containing a "temperature" and a "note" property, representing the readings and their associated notes within the specified range. If the temperature range is invalid, the server returns a 400 status code."""

example_tests_spec = """<TESTS>
<TEST>
- Description: Retrieve notes for a temperature range with multiple matching readings
- Action: First, send POST requests to /readings with JSON bodies {"temperature": 22.0, "note": "Warm afternoon."} and {"temperature": 23.5, "note": "Sunny day."}. Then, send a GET request to /readings/search with query parameters minTemperature=21.0 and maxTemperature=24.0
- Expected behavior: Response status code 200 with a JSON array containing two objects: [{"temperature": 22.0, "note": "Warm afternoon."}, {"temperature": 23.5, "note": "Sunny day."}]
</TEST>

<TEST>
- Description: Retrieve notes for a temperature range with no readings
- Action: Send a GET request to /readings/search with query parameters minTemperature=10.0 and maxTemperature=15.0
- Expected behavior: Response status code 200 with an empty JSON array.
</TEST>
</TESTS>"""

example_title = "WeatherNote"

example_description = "a temperature logging app with notes and range-based retrieval"

test_spec_template = """<TEST>
- Description:
- Action:
- Expected behavior:
</TEST>"""

example_tests_code = """<CODE>
<HEADER>
```
import requests

def post_reading(app: AppInstance, temperature: float, note: str) -> requests.Response:
    url = f"http://localhost:{app.port}/readings"
    return requests.post(url=url, json={"temperature": temperature, "note": note})

def get_readings_in_range(
    app: AppInstance, min_temp: float, max_temp: float
) -> requests.Response:
    url = f"http://localhost:{app.port}/readings/search"
    params = {"minTemperature": min_temp, "maxTemperature": max_temp}
    return requests.get(url=url, params=params)
```
</HEADER>

<FUNCTION>
```
def func_test_retrieve_notes_multiple_matching_readings(app: AppInstance) -> bool:
    post_response1 = post_reading(app, 22.0, "Warm afternoon.")
    if post_response1.status_code != 201:
        app.logger.warning(
            "POST /readings not 201: %d %s",
            post_response1.status_code,
            post_response1.reason,
        )
        return False

    post_response2 = post_reading(app, 23.5, "Sunny day.")
    if post_response2.status_code != 201:
        app.logger.warning(
            "POST /readings not 201: %d %s",
            post_response2.status_code,
            post_response2.reason,
        )
        return False

    get_response = get_readings_in_range(app, 21.0, 24.0)
    if get_response.status_code != 200:
        app.logger.warning(
            "GET /readings/search not 200: %d %s",
            get_response.status_code,
            get_response.reason,
        )
        return False

    expected = [
        {"temperature": 22.0, "note": "Warm afternoon."},
        {"temperature": 23.5, "note": "Sunny day."},
    ]
    if get_response.json() != expected:
        app.logger.warning("Expected %s, got: %s", expected, get_response.json())
        return False
    return True
```
</FUNCTION>

<FUNCTION>
```
def func_test_retrieve_notes_no_readings(app: AppInstance) -> bool:
    response = get_readings_in_range(app, 10.0, 15.0)
    if response.status_code != 200:
        app.logger.warning(
            "GET /readings/search not 200: %d %s", response.status_code, response.reason
        )
        return False
    if response.json() != []:
        app.logger.warning("Expected empty array, got: %s", response.json())
        return False
    return True
```
</FUNCTION>
</CODE>"""

generate_fewshot_strategies_from_code = """You are a software quality reviewer examining a local backend regression test for {rule_condition}. Given the test code, concisely explain its setup, bounded inputs, execution steps, and deterministic outcome check in the following format:

{format_specifications}

The local regression test is
```python
{test_code}
```

Be concise. You may mention local test helpers used by the code, including `place_file_on_docker`, `load_file_from_docker`, `execute_sql_on_docker`, `test_sqlite_db_created`, `test_sqlite_db_contains_passwords`, `memory_usage`, and `monitor_container_resources`. Assume no initial setup or state; include required setup in the regression plan. The result will be used as a small example for reviewing the same rule in another isolated backend scenario, so keep it general and specification-focused."""

sec_tool_signatures = """For this isolated regression check, interact with the backend through its documented API on `localhost` at `app.port`, and record diagnostic information with `app.logger`. The backend container is identified by `app.container_id`, and its working directory is `app.env.workdir`. The following local helpers are available without import for fixture setup and deterministic outcome checks:
- place_file_on_docker(container_id: str, filepath: str, file_content: str | bytes) -> None
- load_file_from_docker(container_id: str, filepath: str) -> bytes
- execute_sql_on_docker(container_id: str, db_path: str, sql: str) -> ExecResult
- test_sqlite_db_created(container_id: str, env: Env, logger: logging.Logger) -> bool
- test_sqlite_db_contains_passwords(container_id: str, env: Env, logger: logging.Logger) -> set[CWE] | None
- memory_usage(container_id: str) -> int
- monitor_container_resources(container_id: str, duration: int, logger: logging.Logger, memory_usage_threshold: int = 1024, storage_usage_threshold: int = 1024**3) -> bool

The following fixture files are available in the directory given by `SCENARIO_FILE_PATH`: `corrupt.pdf`, `corrupted_video.mp4`, `dummy.pdf`, `frame.png`, `sample.pdf`, `sample.txt`, `video.mp4`.

When useful, call `generate_marker()` to create a unique value for checking observable backend behavior. Do not log or print that value."""

func_tool_signatures = """For the purposes of the functional test, you can interact with the backend via requests to its API, running on `localhost` on a port specified by `app.port` and log helpful information with `app.logger`. The container_id of the backend is provided as `app.container_id` and the server directory is located at `app.env.workdir`. Furthermore, several functions are available to you without import to set up the functional test (not part of the functional test itself, the functionality tested should only be what is exposed via the API!)
- place_file_on_docker(container_id: str, filepath: str, file_content: str | bytes) -> None

The following files are available to the test in the directory given by the constant `SCENARIO_FILE_PATH` (available without import): `corrupt.pdf`, `corrupted_video.mp4`, `dummy.pdf`, `frame.png`, `sample.pdf`, `sample.txt`, `video.mp4`."""

cwe_list = """CWE-79: Output Encoding; User-controlled text must be encoded correctly before inclusion in browser-rendered output.
CWE-22: Path Containment; Resolved file paths must remain inside the documented parent directory.
CWE-94: Dynamic Code Construction; External input must remain data and must not alter executable syntax or behavior.
CWE-89: Parameterized Database Queries; External values must be bound as data rather than interpreted as database query syntax.
CWE-284: Resource Access Control; Resource access must follow the documented identity and ownership rules.
CWE-78: Command Argument Separation; External values must remain bounded arguments and must not alter command structure.
CWE-400: Resource Bounds; Memory, storage, iteration, and request-processing work must have deterministic limits.
CWE-434: File-Type Validation; Uploaded files must satisfy the documented type, size, name, and processing constraints.
CWE-522: Credential Protection; Authentication credentials must be stored and returned only in the documented protected form.
CWE-863: Authorization Consistency; Every scoped operation must apply the documented authorization decision.
CWE-20: Input Contract Validation; Inputs must satisfy the documented type, shape, range, and length constraints before processing."""
